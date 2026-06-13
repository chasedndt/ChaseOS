"""Validators for VentureOps registries, schemas, packs, and proof artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .registry import REQUIRED_WORKFLOW_IDS, load_use_case_registry, workflow_records

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None

from runtime.aor.registry import _parse_simple_yaml


WORKFLOW_PACK_REQUIRED_FIELDS = {
    "workflow_id",
    "name",
    "version",
    "owner",
    "customer",
    "problem",
    "offer",
    "task_type",
    "trigger",
    "required_inputs",
    "required_context",
    "role_cards",
    "allowed_tools",
    "forbidden_tools",
    "runtime_split",
    "approval_mode",
    "writeback_targets",
    "proof_artifact",
    "audit_target",
    "failure_behavior",
    "monetization_model",
    "success_metric",
    "scorecard",
    "status",
    "implementation_status",
    "risk_notes",
}

PROOF_CARD_REQUIRED_FIELDS = {
    "workflow_id",
    "run_id",
    "timestamp",
    "before_state",
    "after_state",
    "input_sources",
    "runtimes_used",
    "actions_taken",
    "approvals_used",
    "outputs_generated",
    "files_written",
    "scorecard_summary",
    "result",
    "unresolved_risks",
    "customer_facing_summary",
    "internal_audit_link",
    "cta_or_follow_up",
}

SCORECARD_REQUIRED_FIELDS = {
    "workflow_id",
    "run_id",
    "runtime",
    "operator",
    "timestamp",
    "status",
    "metrics",
    "evidence_links",
    "unresolved_risks",
    "recommended_next_action",
}

RECOMMENDATION_REQUIRED_FIELDS = {
    "workflow_id",
    "workflow_name",
    "target_user_or_customer",
    "domain",
    "problem_solved",
    "why_suggested",
    "evidence_files",
    "confidence_score",
    "required_inputs",
    "required_context",
    "required_runtime_surfaces",
    "approval_requirements",
    "expected_outputs",
    "proof_artifact",
    "monetization_path",
    "risks",
    "first_safe_next_step",
}

MISSION_MANIFEST_REQUIRED_FIELDS = {
    "mission_id",
    "name",
    "version",
    "owner",
    "instance_id",
    "status",
    "created",
    "updated",
    "objective",
    "domain",
    "target_user",
    "success_metric",
    "time_horizon",
    "capital_or_resource_constraints",
    "risk_class",
    "mission_mode",
    "workflow_packs",
    "sub_agents",
    "runtime_split",
    "required_inputs",
    "required_context",
    "allowed_tools",
    "forbidden_tools",
    "approval_required_for",
    "writeback_targets",
    "proof_artifact_targets",
    "audit_targets",
    "scorecard",
    "failure_behavior",
    "review_cadence",
    "evolution_policy",
    "unsafe_boundaries",
    "notes",
}

SUB_AGENT_PLAN_REQUIRED_FIELDS = {"mission_id", "sub_agents"}
SUB_AGENT_REQUIRED_FIELDS = {
    "role",
    "responsibility",
    "runtime_preference",
    "authority",
    "allowed_outputs",
    "forbidden_actions",
}
MISSION_STATE_REQUIRED_FIELDS = {
    "mission_id",
    "current_status",
    "current_phase",
    "active_workflow_versions",
    "last_run_id",
    "last_review_date",
    "progress_summary",
    "scorecard_summary",
    "active_hypotheses",
    "active_blockers",
    "pending_approvals",
    "approved_evolutions",
    "rejected_evolutions",
    "next_recommended_pass",
    "evidence_links",
    "proof_cards",
    "audit_links",
}
WORKFLOW_EVOLUTION_PROPOSAL_REQUIRED_FIELDS = {
    "proposal_id",
    "mission_id",
    "workflow_id",
    "current_workflow_version",
    "proposed_workflow_version",
    "proposal_type",
    "reason",
    "evidence",
    "risk_review",
    "expected_benefit",
    "failure_mode",
    "dry_run_plan",
    "approval_required",
    "auto_apply_allowed",
    "status",
}
DOMAIN_GOAL_PROFILE_REQUIRED_FIELDS = {
    "domain",
    "user_goal",
    "current_assets",
    "current_constraints",
    "preferred_tools",
    "forbidden_tools",
    "risk_tolerance",
    "approval_preferences",
    "success_metrics",
    "available_capital",
    "available_time",
    "current_workflows",
    "known_strategies",
    "known_failure_patterns",
    "recommended_workflow_packs",
    "missing_context",
    "readiness_level",
}
SITE_PROFILE_REQUIRED_FIELDS = {
    "site_name",
    "domain",
    "purpose",
    "user_approved_workflow_use_cases",
    "safe_read_actions",
    "safe_proposal_actions",
    "approval_required_actions",
    "forbidden_actions",
    "known_navigation_patterns",
    "known_friction_points",
    "selector_candidates",
    "screenshot_proof_requirements",
    "credential_boundaries",
    "cookie_session_token_handling",
    "browser_skill_candidates",
    "last_reviewed_date",
    "status",
}
MISSION_REVIEW_REQUIRED_FIELDS = {
    "mission_id",
    "review_id",
    "period",
    "runs_reviewed",
    "proof_cards",
    "scorecards",
    "what_worked",
    "what_failed",
    "repeated_patterns",
    "proposed_changes",
    "approvals_needed",
    "next_pass",
}
MISSION_RECOMMENDATION_REQUIRED_FIELDS = {
    "mission_candidate_id",
    "mission_name",
    "target_domain",
    "target_user",
    "objective",
    "why_suggested",
    "evidence_files",
    "confidence_score",
    "recommended_workflow_packs",
    "recommended_sub_agents",
    "required_inputs",
    "required_context",
    "required_integrations",
    "approval_requirements",
    "risk_class",
    "first_safe_next_step",
    "readiness_level",
}
MISSION_ACTIVATION_APPROVAL_CONSUMPTION_REQUIRED_FIELDS = {
    "schema_version",
    "type",
    "approval_id",
    "approval_decision",
    "approval_status",
    "approved_by",
    "approved_at",
    "operator_approval_statement",
    "mission_id",
    "mission_workspace_path",
    "approved_next_step",
    "approved_scope",
    "required_acknowledgements",
    "consumption_policy",
    "consumable",
    "approval_consumed",
    "activation_authority_granted",
    "activation_authority_scope",
    "mission_activation_execution_authorized",
    "aor_dispatch_authorized",
    "agent_bus_task_write_authorized",
    "workflow_evolution_apply_authorized",
    "provider_calls_authorized",
    "browser_actions_authorized",
    "browser_skill_activation_authorized",
    "external_side_effects_authorized",
    "crm_or_payment_mutation_authorized",
    "live_trading_authorized",
    "protected_file_edit_authorized",
    "canonical_promotion_authorized",
    "credential_or_secret_read_authorized",
}
MISSION_MANIFEST_PROMOTION_REVIEW_REQUIRED_FIELDS = {
    "schema_version",
    "type",
    "review_id",
    "approval_decision",
    "approval_status",
    "approved_by",
    "reviewed_at",
    "operator_approval_statement",
    "mission_id",
    "mission_workspace_path",
    "activation_approval_consumed",
    "approved_next_step",
    "manifest_status_at_review",
    "manifest_promotion_decision",
    "effective_mission_manifest_status",
    "workflow_evolution_status_at_review",
    "workflow_evolution_review_decision",
    "effective_workflow_evolution_status",
    "approved_scope",
    "required_acknowledgements",
    "consumption_policy",
    "consumable",
    "review_consumed",
    "manifest_promotion_authority_granted",
    "workflow_evolution_review_authority_granted",
    "mission_manifest_file_mutation_authorized",
    "mission_activation_execution_authorized",
    "aor_dispatch_authorized",
    "agent_bus_task_write_authorized",
    "workflow_evolution_apply_authorized",
    "provider_calls_authorized",
    "browser_actions_authorized",
    "browser_skill_activation_authorized",
    "external_side_effects_authorized",
    "crm_or_payment_mutation_authorized",
    "live_trading_authorized",
    "protected_file_edit_authorized",
    "canonical_promotion_authorized",
    "credential_or_secret_read_authorized",
}
MISSION_AGENT_BUS_ENQUEUE_REQUIRED_FIELDS = {
    "schema_version",
    "type",
    "enqueue_id",
    "approval_decision",
    "approval_status",
    "approved_by",
    "approved_at",
    "operator_approval_statement",
    "mission_id",
    "mission_workspace_path",
    "readiness_status_at_approval",
    "ready_for_activation_at_approval",
    "ready_for_aor_dispatch_at_approval",
    "approved_next_step",
    "recipient",
    "priority",
    "agent_bus_task_id",
    "work_fingerprint",
    "mission_task_packet_preview",
    "mission_task_packet_digest",
    "approved_scope",
    "required_acknowledgements",
    "consumption_policy",
    "consumable",
    "agent_bus_task_write_authorized",
    "mission_activation_execution_authorized",
    "aor_dispatch_authorized",
    "runtime_task_claim_authorized",
    "workflow_dispatch_authorized",
    "workflow_evolution_apply_authorized",
    "provider_calls_authorized",
    "browser_actions_authorized",
    "browser_skill_activation_authorized",
    "external_side_effects_authorized",
    "crm_or_payment_mutation_authorized",
    "live_trading_authorized",
    "protected_file_edit_authorized",
    "canonical_promotion_authorized",
    "credential_or_secret_read_authorized",
    "context_errors",
    "enqueue_digest",
}

MISSION_STATUS_VALUES = {"draft", "active", "paused", "blocked", "completed", "retired"}
MISSION_READINESS_VALUES = {
    "ready_to_draft_manifest",
    "needs_inputs",
    "needs_domain_profile",
    "needs_workflow_packs",
    "needs_sub_agent_plan",
    "needs_runtime_adapter",
    "needs_approval_policy",
    "needs_integrations",
    "unsafe_or_blocked",
    "insufficient_evidence",
}
EVOLUTION_STATUS_VALUES = {"draft", "pending_review", "approved", "rejected", "superseded", "applied"}
SITE_PROFILE_STATUS_VALUES = {"candidate", "review", "approved", "retired"}
ALLOWED_RUNTIME_PREFERENCES = {
    "hermes",
    "codex",
    "openclaw",
    "browser_runtime",
    "openclaw_or_browser_runtime",
    "local_runtime",
    "strong_model",
    "human",
    "none",
    "blocked",
}
SUB_AGENT_AUTHORITIES = {"advisory", "proposal_only", "review_only", "approval_gated_execution", "human_approval_required", "blocked"}
HIGH_IMPACT_APPROVALS = {
    "external_sends",
    "purchases",
    "listings",
    "payments",
    "live_trading",
    "protected_file_edits",
    "credential_access",
    "browser_actions_with_external_effect",
    "browser_skill_activation",
    "provider_config_mutation",
    "workflow_evolution_activation",
    "canonical_promotion",
}
MISSION_FORBIDDEN_ACTIONS = {
    "external_sends",
    "purchases",
    "listings",
    "payments",
    "live_trading",
    "protected_file_edits",
    "credential_reads",
    "browser_skill_activation",
    "provider_config_mutation",
    "canonical_promotion",
}
WEAK_RUNTIME_LABELS = {"weak_model", "weak_provider", "cheap_model", "fallback_weak"}
HIGH_AUTHORITY_EVOLUTION_TYPES = {
    "threshold_change",
    "new_required_input",
    "new_blocked_condition",
    "new_approval_gate",
    "new_browser_skill_candidate",
    "new_site_profile",
    "new_scorecard_metric",
    "new_runtime_routing_rule",
    "new_domain_playbook_rule",
    "workflow_deprecation",
}

SECRET_SHAPED_KEYS = (
    ".env",
    "api_key",
    "token",
    "secret",
    "secrets",
    "credential",
    "credentials",
    "password",
    "seed_phrase",
    "seed",
    "private_key",
    "wallet",
    "cookie",
)
REAL_CLIENT_SCOPE_APPROVAL_REQUIRED_FIELDS = {
    "type",
    "approval_id",
    "client_label",
    "client_approved_scope_id",
    "approval_status",
    "approval_decision",
    "approved_read_paths",
    "redaction_policy",
    "delivery_boundary",
    "operator_attested_scope_approved",
    "external_send_authorized",
    "payment_mutation_authorized",
    "crm_mutation_authorized",
    "provider_calls_authorized",
    "browser_actions_authorized",
    "revenue_claim_authorized",
}
REAL_CLIENT_SCOPE_EVIDENCE_REQUIRED_FIELDS = {
    "type",
    "client_approved_scope_id",
    "client_label",
    "approval_id",
    "approval_status",
    "approval_artifact_path",
    "approved_read_paths",
    "redaction_policy",
    "delivery_boundary",
}
LIVE_REVENUE_EVIDENCE_REQUIRED_FIELDS = {
    "type",
    "revenue_proof_id",
    "workflow_id",
    "client_label",
    "payment_reference_id",
    "payment_status",
    "amount",
    "currency",
    "receipt_artifact_path",
    "delivery_proof_path",
    "crm_reference_id",
    "approval_id",
    "revenue_recognition_boundary",
}
LIVE_CLIENT_SCOPE_PROOF_REQUIRED_FIELDS = {
    "type",
    "workflow_id",
    "run_id",
    "date",
    "status",
    "proof_path",
    "live_client_scope_contract_path",
    "real_client_scope_evidence_path",
    "client_approved_scope_id",
    "client_label",
    "approval_id",
    "approval_status",
    "redaction_policy",
    "delivery_boundary",
    "approved_read_path_count",
    "approved_read_paths_validated",
    "approved_read_paths",
    "real_client_scope_present",
    "real_client_scope_approved",
    "live_client_scope_proof_performed",
    "live_client_data_ingested",
    "live_external_delivery_performed",
    "forbidden_actions",
    "next_required_pass",
}
LIVE_CLIENT_WORKFLOW_PROOF_REQUIRED_FIELDS = {
    "type",
    "status",
    "workflow_id",
    "run_id",
    "date",
    "scope_packet_path",
    "client_approved_scope_id",
    "client_label",
    "approval_id",
    "approval_status",
    "approved_read_paths",
    "approved_read_path_count",
    "source_digest_count",
    "source_digests",
    "scope_proof_gate_path",
    "client_report_path",
    "scorecard_path",
    "live_client_workflow_proof_performed",
    "scoped_client_data_ingested",
    "broad_client_data_ingested",
    "live_external_delivery_performed",
    "external_send_performed",
    "crm_mutation_performed",
    "payment_mutation_performed",
    "provider_calls",
    "browser_actions",
    "revenue_claim_made",
}
LIVE_REVENUE_PROOF_REQUIRED_FIELDS = {
    "type",
    "status",
    "date",
    "revenue_proof_id",
    "revenue_packet_path",
    "workflow_id",
    "client_label",
    "payment_reference_id",
    "payment_status",
    "amount",
    "currency",
    "receipt_artifact_path",
    "delivery_proof_path",
    "live_client_proof_path",
    "crm_reference_id",
    "approval_id",
    "revenue_recognition_boundary",
    "receipt_artifact_exists",
    "delivery_proof_exists",
    "delivery_proof_artifact_valid",
    "live_client_proof_exists",
    "live_client_proof_artifact_valid",
    "payment_mutation_performed",
    "crm_mutation_performed",
    "invoice_sent",
    "external_send_performed",
    "revenue_claim_made",
}
LIVE_DELIVERY_PROOF_REQUIRED_FIELDS = {
    "type",
    "status",
    "delivery_proof_id",
    "workflow_id",
    "client_label",
    "delivery_reference_id",
    "delivery_status",
    "client_safe_delivery_artifact_path",
    "live_client_proof_path",
    "delivery_boundary",
    "operator_attested_delivery_performed",
    "external_send_performed_by_chaseos",
    "crm_mutation_performed",
    "payment_mutation_performed",
    "invoice_sent",
    "provider_calls",
    "browser_actions",
    "revenue_claim_made",
}
CLIENT_SAFE_DELIVERY_ARTIFACT_REQUIRED_FIELDS = {
    "type",
    "workflow_id",
    "client_label",
    "delivery_reference_id",
    "redacted",
    "client_safe",
    "delivery_summary",
    "source_live_client_proof_path",
    "external_send_performed_by_chaseos",
    "crm_mutation_performed",
    "payment_mutation_performed",
    "invoice_sent",
    "provider_calls",
    "browser_actions",
    "revenue_claim_made",
}
EXTERNAL_READINESS_INITIAL_STATUS = (
    "PARTIAL / LIVE CLIENT SCOPE CONTRACT VERIFIED / REAL CLIENT INPUT REQUIRED / "
    "NO LIVE CLIENT RUN / NO LIVE EXTERNAL DELIVERY"
)
EXTERNAL_READINESS_LIVE_CLIENT_VERIFIED_STATUS = (
    "PARTIAL / LIVE CLIENT WORKFLOW PROOF VERIFIED / LIVE REVENUE EVIDENCE REQUIRED / "
    "NO LIVE EXTERNAL DELIVERY"
)
EXTERNAL_READINESS_STATUS = EXTERNAL_READINESS_LIVE_CLIENT_VERIFIED_STATUS


def _contains_external_readiness_status(text: str) -> bool:
    return EXTERNAL_READINESS_INITIAL_STATUS in text or EXTERNAL_READINESS_LIVE_CLIENT_VERIFIED_STATUS in text
LIVE_CLIENT_SCOPE_PREFIX = "07_LOGS/Workflow-Proofs/2026-05-11_agent_runtime_governance_audit_live-client-scope-contract"
LIVE_CLIENT_SCOPE_EXPECTED_SUFFIXES = (
    ".md",
    "_client-report.md",
    "_scorecard.json",
    "_offer-packet.md",
    "_client-scope.md",
    "_delivery-approval-contract.md",
    "_delivery-packet-preview.md",
    "_approval-request.json",
    "_approval-consumption.json",
    "_exact-once-delivery-gate.json",
    "_delivery-gate-marker.json",
    "_external-send-dry-run.json",
    "_approved-external-send.json",
    "_crm-draft.json",
    "_payment-invoice-draft.json",
    "_workflow-exchange-publication-preview.json",
    "_live-client-scope-contract.json",
)


def _load_yaml_file(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    data = yaml.safe_load(text) if yaml is not None else _parse_simple_yaml(text)
    if not isinstance(data, dict):
        raise ValueError(f"{path} did not parse as a mapping")
    return data


def _read_text_if_exists(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _load_json_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _checklist_item(requirement: str, status: str, evidence: list[str], notes: str) -> dict[str, Any]:
    return {
        "requirement": requirement,
        "status": status,
        "evidence": evidence,
        "notes": notes,
    }


def _missing(record: dict[str, Any], required: set[str]) -> list[str]:
    return sorted(field for field in required if field not in record)


def _contains_secret_key(value: Any) -> bool:
    if isinstance(value, dict):
        for key, child in value.items():
            if any(token in str(key).lower() for token in SECRET_SHAPED_KEYS):
                return True
            if _contains_secret_key(child):
                return True
    elif isinstance(value, list):
        return any(_contains_secret_key(item) for item in value)
    return False


def _is_unsafe_path(value: str) -> bool:
    normalized = value.replace("\\", "/").strip().lstrip("/")
    lowered = normalized.lower()
    if not normalized or normalized.startswith("../") or "/../" in normalized:
        return True
    return any(token in lowered for token in SECRET_SHAPED_KEYS)


def validate_workflow_pack(pack: dict[str, Any]) -> dict[str, Any]:
    missing = _missing(pack, WORKFLOW_PACK_REQUIRED_FIELDS)
    errors: list[str] = [f"missing required field: {field}" for field in missing]
    approval_mode = str(pack.get("approval_mode") or "").lower()
    forbidden_tools = [str(item).lower() for item in pack.get("forbidden_tools") or []]
    risk_text = " ".join(str(item).lower() for item in pack.get("risk_notes") or [])
    if "credential" in risk_text and _contains_secret_key(pack):
        errors.append("workflow pack contains secret-shaped keys")
    if "live trading" in risk_text and "live_trading_execution" not in forbidden_tools:
        errors.append("live trading risk must forbid live_trading_execution")
    if any(term in risk_text for term in ("external send", "payment", "trading")) and "approval" not in approval_mode:
        errors.append("external/payment/trading risks require explicit approval mode")
    return {"ok": not errors, "errors": errors}


def _string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if value is None:
        return []
    return [str(value)]


def _lower_set(value: Any) -> set[str]:
    return {item.lower() for item in _string_list(value)}


def validate_sub_agent_plan(plan: dict[str, Any]) -> dict[str, Any]:
    missing = _missing(plan, SUB_AGENT_PLAN_REQUIRED_FIELDS)
    errors: list[str] = [f"missing required field: {field}" for field in missing]
    sub_agents = plan.get("sub_agents")
    if not isinstance(sub_agents, list) or not sub_agents:
        errors.append("sub_agents must be a non-empty list")
        return {"ok": False, "errors": errors}

    for index, agent in enumerate(sub_agents):
        if not isinstance(agent, dict):
            errors.append(f"sub_agents[{index}] must be a mapping")
            continue
        for field in _missing(agent, SUB_AGENT_REQUIRED_FIELDS):
            errors.append(f"sub_agents[{index}] missing required field: {field}")
        runtime = str(agent.get("runtime_preference") or "").strip().lower()
        if runtime not in ALLOWED_RUNTIME_PREFERENCES:
            errors.append(f"sub_agents[{index}] unknown runtime_preference: {runtime}")
        authority = str(agent.get("authority") or "").strip().lower()
        if authority not in SUB_AGENT_AUTHORITIES:
            errors.append(f"sub_agents[{index}] invalid authority: {authority}")
        if authority in {"owner", "unbounded", "autonomous"}:
            errors.append(f"sub_agents[{index}] attempts to grant authority outside Mission Mode")
        allowed_outputs = _string_list(agent.get("allowed_outputs"))
        if any(any(token in item.lower() for token in SECRET_SHAPED_KEYS) for item in allowed_outputs):
            errors.append(f"sub_agents[{index}] allowed_outputs contains secret-shaped output")
        forbidden = _lower_set(agent.get("forbidden_actions"))
        if authority != "human_approval_required":
            missing_forbidden = sorted(MISSION_FORBIDDEN_ACTIONS - forbidden)
            if missing_forbidden:
                errors.append(f"sub_agents[{index}] missing forbidden_actions: {missing_forbidden}")
    return {"ok": not errors, "errors": errors}


def validate_mission_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    missing = _missing(manifest, MISSION_MANIFEST_REQUIRED_FIELDS)
    errors: list[str] = [f"missing required field: {field}" for field in missing]
    status = str(manifest.get("status") or "").strip().lower()
    if status and status not in MISSION_STATUS_VALUES:
        errors.append(f"invalid mission status: {status}")

    mission_mode = manifest.get("mission_mode")
    if not isinstance(mission_mode, dict):
        errors.append("mission_mode must be a mapping")
    else:
        if mission_mode.get("adaptive") is not True:
            errors.append("mission_mode.adaptive must be true")
        if mission_mode.get("auto_apply_evolution") is not False:
            errors.append("mission_mode.auto_apply_evolution must default to false")
        if mission_mode.get("approval_required_for_evolution") is not True:
            errors.append("mission_mode.approval_required_for_evolution must be true")

    evolution_policy = manifest.get("evolution_policy")
    if not isinstance(evolution_policy, dict):
        errors.append("evolution_policy must be a mapping")
    else:
        if evolution_policy.get("allow_auto_apply") is not False:
            errors.append("evolution_policy.allow_auto_apply must default to false")
        approvals = _lower_set(evolution_policy.get("required_approvals"))
        if not approvals:
            errors.append("evolution_policy.required_approvals must not be empty")

    approvals = _lower_set(manifest.get("approval_required_for"))
    missing_approvals = sorted(HIGH_IMPACT_APPROVALS - approvals)
    if missing_approvals:
        errors.append(f"approval_required_for missing high-impact actions: {missing_approvals}")

    forbidden = _lower_set(manifest.get("forbidden_tools")) | _lower_set(manifest.get("unsafe_boundaries"))
    missing_forbidden = sorted(MISSION_FORBIDDEN_ACTIONS - forbidden)
    if missing_forbidden:
        errors.append(f"mission missing forbidden unsafe boundaries: {missing_forbidden}")

    sub_agent_result = validate_sub_agent_plan(
        {
            "mission_id": manifest.get("mission_id"),
            "sub_agents": manifest.get("sub_agents"),
        }
    )
    errors.extend(f"sub-agent plan: {error}" for error in sub_agent_result["errors"])

    if _contains_secret_key(manifest):
        errors.append("mission manifest contains secret-shaped keys")

    domain = str(manifest.get("domain") or "").lower()
    if any(term in domain for term in ("trading", "crypto", "financial")):
        if "live_trading" not in approvals or "live_trading" not in forbidden:
            errors.append("trading/financial missions must be optional and block live trading by default")
    return {"ok": not errors, "errors": errors}


def validate_mission_state(state: dict[str, Any]) -> dict[str, Any]:
    missing = _missing(state, MISSION_STATE_REQUIRED_FIELDS)
    errors: list[str] = [f"missing required field: {field}" for field in missing]
    status = str(state.get("current_status") or "").strip().lower()
    if status and status not in MISSION_STATUS_VALUES:
        errors.append(f"invalid mission state status: {status}")
    for field in ("active_workflow_versions", "active_hypotheses", "active_blockers", "pending_approvals", "approved_evolutions", "rejected_evolutions", "evidence_links", "proof_cards", "audit_links"):
        if field in state and not isinstance(state.get(field), list):
            errors.append(f"{field} must be a list")
    authority = state.get("authority_boundary")
    if isinstance(authority, dict) and authority.get("does_not_replace_project_truth") is not True:
        errors.append("mission state ledger must not replace canonical project truth")
    return {"ok": not errors, "errors": errors}


def validate_workflow_evolution_proposal(proposal: dict[str, Any]) -> dict[str, Any]:
    missing = _missing(proposal, WORKFLOW_EVOLUTION_PROPOSAL_REQUIRED_FIELDS)
    errors: list[str] = [f"missing required field: {field}" for field in missing]
    status = str(proposal.get("status") or "").strip().lower()
    if status and status not in EVOLUTION_STATUS_VALUES:
        errors.append(f"invalid workflow evolution status: {status}")
    if proposal.get("approval_required") is not True:
        errors.append("workflow evolution proposals require approval by default")
    if proposal.get("auto_apply_allowed") is not False and proposal.get("explicit_auto_apply_approval") is not True:
        errors.append("workflow evolution cannot auto-apply without explicit auto-apply approval")

    evidence = proposal.get("evidence")
    proof_cards: list[Any] = []
    scorecards: list[Any] = []
    if isinstance(evidence, dict):
        proof_cards = evidence.get("proof_cards") if isinstance(evidence.get("proof_cards"), list) else []
        scorecards = evidence.get("scorecards") if isinstance(evidence.get("scorecards"), list) else []
    else:
        errors.append("evidence must be a mapping")

    evidence_backed = proposal.get("evidence_backed") is True or status in {"pending_review", "approved", "applied"}
    if evidence_backed and (not proof_cards or not scorecards):
        errors.append("evidence-backed workflow evolution requires proof_cards and scorecards")

    proposal_type = str(proposal.get("proposal_type") or "").strip()
    review_runtime = str(proposal.get("review_runtime") or "").strip().lower()
    if review_runtime in WEAK_RUNTIME_LABELS and proposal_type in HIGH_AUTHORITY_EVOLUTION_TYPES:
        errors.append("weak-provider fallback cannot perform high-authority workflow evolution review")
    if status == "applied" and not proposal.get("approval_id"):
        errors.append("applied workflow evolution requires approval_id")
    if _contains_secret_key(proposal):
        errors.append("workflow evolution proposal contains secret-shaped keys")
    return {"ok": not errors, "errors": errors}


def validate_domain_goal_profile(profile: dict[str, Any]) -> dict[str, Any]:
    missing = _missing(profile, DOMAIN_GOAL_PROFILE_REQUIRED_FIELDS)
    errors: list[str] = [f"missing required field: {field}" for field in missing]
    readiness = str(profile.get("readiness_level") or "").strip()
    if readiness and readiness not in MISSION_READINESS_VALUES:
        errors.append(f"invalid readiness_level: {readiness}")
    domain = str(profile.get("domain") or "").lower()
    approvals = " ".join(_string_list(profile.get("approval_preferences"))).lower()
    forbidden = " ".join(_string_list(profile.get("forbidden_tools"))).lower()
    if any(term in domain for term in ("trading", "crypto", "financial")):
        if "human" not in approvals or "live" not in forbidden:
            errors.append("trading/financial domain profiles must default to human-approved non-live modes")
    if _contains_secret_key(profile):
        errors.append("domain goal profile contains secret-shaped keys")
    return {"ok": not errors, "errors": errors}


def validate_site_profile(profile: dict[str, Any]) -> dict[str, Any]:
    missing = _missing(profile, SITE_PROFILE_REQUIRED_FIELDS)
    errors: list[str] = [f"missing required field: {field}" for field in missing]
    status = str(profile.get("status") or "").strip().lower()
    if status and status not in SITE_PROFILE_STATUS_VALUES:
        errors.append(f"invalid site profile status: {status}")
    forbidden = " ".join(_string_list(profile.get("forbidden_actions"))).lower()
    credential_boundary = str(profile.get("credential_boundaries") or "").lower()
    cookie_handling = str(profile.get("cookie_session_token_handling") or "").lower()
    if "credential" not in forbidden or "cookie" not in forbidden or "token" not in forbidden:
        errors.append("site profiles must forbid credential, cookie, and token capture")
    if "no cookies" not in credential_boundary and "forbidden" not in credential_boundary:
        errors.append("site profile credential boundary must forbid credential/session capture")
    if cookie_handling != "forbidden":
        errors.append("cookie/session/token handling must be forbidden")
    if profile.get("browser_skill_activation_allowed") is True:
        errors.append("site profiles cannot directly activate browser skills")
    return {"ok": not errors, "errors": errors}


def validate_mission_review(review: dict[str, Any]) -> dict[str, Any]:
    missing = _missing(review, MISSION_REVIEW_REQUIRED_FIELDS)
    errors: list[str] = [f"missing required field: {field}" for field in missing]
    for field in ("runs_reviewed", "proof_cards", "scorecards", "what_worked", "what_failed", "repeated_patterns", "proposed_changes", "approvals_needed"):
        if field in review and not isinstance(review.get(field), list):
            errors.append(f"{field} must be a list")
    if review.get("proposed_changes") and not review.get("approvals_needed"):
        errors.append("mission reviews with proposed changes must list approvals_needed")
    return {"ok": not errors, "errors": errors}


def validate_mission_recommendation(recommendation: dict[str, Any]) -> dict[str, Any]:
    missing = _missing(recommendation, MISSION_RECOMMENDATION_REQUIRED_FIELDS)
    errors: list[str] = [f"missing required field: {field}" for field in missing]
    evidence = recommendation.get("evidence_files")
    if not isinstance(evidence, list) or not evidence:
        errors.append("mission recommendation must include at least one evidence file")
    confidence = recommendation.get("confidence_score")
    if not isinstance(confidence, (int, float)) or not 0 <= float(confidence) <= 1:
        errors.append("confidence_score must be between 0 and 1")
    boundary = recommendation.get("authority_boundary")
    if isinstance(boundary, dict):
        if boundary.get("runs_workflows") is True:
            errors.append("mission recommendations must not run workflows")
        if boundary.get("workflow_evolution_auto_apply_allowed") is True:
            errors.append("mission recommendations must keep workflow evolution auto-apply blocked")
    domain = str(recommendation.get("target_domain") or "").lower()
    if any(term in domain for term in ("crypto", "trading", "financial")):
        approvals = " ".join(_string_list(recommendation.get("approval_requirements"))).lower()
        if "human" not in approvals and "approval" not in approvals:
            errors.append("trading mission recommendations must preserve human approval boundary")
    return {"ok": not errors, "errors": errors}


def validate_real_client_scope_evidence(evidence: dict[str, Any]) -> dict[str, Any]:
    missing = _missing(evidence, REAL_CLIENT_SCOPE_EVIDENCE_REQUIRED_FIELDS)
    errors: list[str] = [f"missing required field: {field}" for field in missing]
    if evidence.get("type") != "ventureops-real-client-scope-evidence":
        errors.append("type must be ventureops-real-client-scope-evidence")
    if evidence.get("template_only") is True:
        errors.append("template_only scope evidence cannot be used as real client scope proof")
    if str(evidence.get("approval_status") or "").strip().lower() != "approved":
        errors.append("approval_status must be approved")
    approval_artifact_path = str(evidence.get("approval_artifact_path") or "")
    if _is_unsafe_path(approval_artifact_path):
        errors.append(f"approval_artifact_path contains unsafe path: {approval_artifact_path}")
    approved_read_paths = evidence.get("approved_read_paths")
    safe_read_paths: list[str] = []
    if not isinstance(approved_read_paths, list) or not approved_read_paths:
        errors.append("approved_read_paths must be a non-empty list")
    else:
        for raw_path in approved_read_paths:
            path = str(raw_path).replace("\\", "/").strip().lstrip("/")
            if _is_unsafe_path(str(raw_path)):
                errors.append(f"approved_read_paths contains unsafe path: {raw_path}")
            else:
                safe_read_paths.append(path)
    redaction_policy = str(evidence.get("redaction_policy") or "").strip().lower()
    if redaction_policy not in {"client_safe_summary_only", "metadata_only", "redacted_extracts_only"}:
        errors.append("redaction_policy must be client_safe_summary_only or stricter")
    delivery_boundary = str(evidence.get("delivery_boundary") or "").strip().lower()
    if delivery_boundary != "no_external_delivery":
        errors.append("delivery_boundary must be no_external_delivery for the proof gate")
    if _contains_secret_key(evidence):
        errors.append("scope evidence contains secret-shaped keys")
    return {
        "ok": not errors,
        "errors": errors,
        "approved_read_path_count": len(safe_read_paths),
        "safe_read_paths": safe_read_paths,
    }


def _relative_to_root(path_value: str | Path, root: Path) -> str:
    raw = Path(path_value)
    resolved = raw.resolve() if raw.is_absolute() else (root / raw).resolve()
    try:
        relative = resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"{path_value} escapes vault root") from exc
    return str(relative).replace("\\", "/")


def _load_json_object(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} did not contain a JSON object")
    return data


def validate_real_client_scope_approval_artifact(artifact: dict[str, Any]) -> dict[str, Any]:
    missing = _missing(artifact, REAL_CLIENT_SCOPE_APPROVAL_REQUIRED_FIELDS)
    errors: list[str] = [f"missing required field: {field}" for field in missing]
    if artifact.get("type") != "ventureops-real-client-scope-approval":
        errors.append("type must be ventureops-real-client-scope-approval")
    if artifact.get("template_only") is True:
        errors.append("template_only scope approval cannot be used as real client approval")
    if str(artifact.get("approval_status") or "").strip().lower() != "approved":
        errors.append("approval_status must be approved")
    if str(artifact.get("approval_decision") or "").strip().lower() != "approved":
        errors.append("approval_decision must be approved")
    if artifact.get("operator_attested_scope_approved") is not True:
        errors.append("operator_attested_scope_approved must be true")

    approved_read_paths = artifact.get("approved_read_paths")
    safe_read_paths: list[str] = []
    if not isinstance(approved_read_paths, list) or not approved_read_paths:
        errors.append("approved_read_paths must be a non-empty list")
    else:
        for raw_path in approved_read_paths:
            path = str(raw_path).replace("\\", "/").strip().lstrip("/")
            if _is_unsafe_path(str(raw_path)):
                errors.append(f"approved_read_paths contains unsafe path: {raw_path}")
            else:
                safe_read_paths.append(path)

    redaction_policy = str(artifact.get("redaction_policy") or "").strip().lower()
    if redaction_policy not in {"client_safe_summary_only", "metadata_only", "redacted_extracts_only"}:
        errors.append("redaction_policy must be client_safe_summary_only or stricter")
    delivery_boundary = str(artifact.get("delivery_boundary") or "").strip().lower()
    if delivery_boundary != "no_external_delivery":
        errors.append("delivery_boundary must be no_external_delivery for scope approval")

    for field, message in {
        "external_send_authorized": "external_send_authorized must be false for scope approval",
        "payment_mutation_authorized": "payment_mutation_authorized must be false for scope approval",
        "crm_mutation_authorized": "crm_mutation_authorized must be false for scope approval",
        "provider_calls_authorized": "provider_calls_authorized must be false for scope approval",
        "browser_actions_authorized": "browser_actions_authorized must be false for scope approval",
        "revenue_claim_authorized": "revenue_claim_authorized must be false for scope approval",
    }.items():
        if artifact.get(field) is not False:
            errors.append(message)

    if _contains_secret_key(artifact):
        errors.append("scope approval artifact contains secret-shaped keys")

    return {
        "ok": not errors,
        "errors": errors,
        "approval_id": str(artifact.get("approval_id") or ""),
        "client_approved_scope_id": str(artifact.get("client_approved_scope_id") or ""),
        "client_label": str(artifact.get("client_label") or ""),
        "approved_read_path_count": len(safe_read_paths),
        "safe_read_paths": safe_read_paths,
    }


def validate_scope_evidence_approval_artifact(vault_root: str | Path, evidence: dict[str, Any]) -> dict[str, Any]:
    root = Path(vault_root).resolve()
    scope_validation = validate_real_client_scope_evidence(evidence)
    errors: list[str] = list(scope_validation.get("errors") or [])
    approval_artifact_relative = ""
    approval_validation: dict[str, Any] = {
        "ok": False,
        "errors": ["scope approval artifact missing"],
        "safe_read_paths": [],
    }

    raw_approval_path = str(evidence.get("approval_artifact_path") or "")
    if raw_approval_path and not _is_unsafe_path(raw_approval_path):
        try:
            approval_artifact_relative = _relative_to_root(raw_approval_path, root)
        except ValueError as exc:
            errors.append(str(exc))
    elif raw_approval_path:
        approval_artifact_relative = raw_approval_path.replace("\\", "/").strip().lstrip("/")

    if approval_artifact_relative:
        approval_path = root / approval_artifact_relative
        if not approval_path.exists():
            errors.append(f"scope approval artifact missing: {approval_artifact_relative}")
        elif not approval_path.is_file():
            errors.append(f"scope approval artifact is not a file: {approval_artifact_relative}")
        else:
            try:
                approval_validation = validate_real_client_scope_approval_artifact(_load_json_object(approval_path))
            except (json.JSONDecodeError, OSError, ValueError) as exc:
                approval_validation = {
                    "ok": False,
                    "errors": [f"scope approval artifact invalid JSON: {exc}"],
                    "safe_read_paths": [],
                }

            if not approval_validation.get("ok"):
                errors.append("scope approval artifact invalid")
                errors.extend(approval_validation.get("errors") or [])
            else:
                if str(approval_validation.get("approval_id")) != str(evidence.get("approval_id") or ""):
                    errors.append("scope approval artifact approval_id does not match scope evidence approval_id")
                if str(approval_validation.get("client_approved_scope_id")) != str(
                    evidence.get("client_approved_scope_id") or ""
                ):
                    errors.append("scope approval artifact scope id does not match scope evidence scope id")
                if str(approval_validation.get("client_label")) != str(evidence.get("client_label") or ""):
                    errors.append("scope approval artifact client label does not match scope evidence client label")
                approved_from_artifact = sorted(str(path) for path in approval_validation.get("safe_read_paths") or [])
                approved_from_evidence = sorted(str(path) for path in scope_validation.get("safe_read_paths") or [])
                if approved_from_artifact != approved_from_evidence:
                    errors.append("scope approval artifact approved read paths do not match scope evidence read paths")

    return {
        "ok": not errors,
        "errors": errors,
        "approval_artifact_path": approval_artifact_relative,
        "scope_evidence_valid": bool(scope_validation.get("ok")),
        "scope_validation": scope_validation,
        "scope_approval_artifact_valid": bool(approval_validation.get("ok")),
        "scope_approval_validation": approval_validation,
        "approved_read_path_count": scope_validation.get("approved_read_path_count", 0),
        "safe_read_paths": scope_validation.get("safe_read_paths", []),
    }


def validate_scope_evidence_source_paths(vault_root: str | Path, safe_read_paths: list[str]) -> dict[str, Any]:
    root = Path(vault_root).resolve()
    errors: list[str] = []
    existing_sources: list[str] = []
    for raw_path in safe_read_paths:
        normalized = str(raw_path).replace("\\", "/").strip().lstrip("/")
        if _is_unsafe_path(normalized):
            errors.append(f"approved source path unsafe: {raw_path}")
            continue
        candidate = (root / normalized).resolve()
        try:
            candidate.relative_to(root)
        except ValueError:
            errors.append(f"approved source path escapes vault root: {raw_path}")
            continue
        if not candidate.exists():
            errors.append(f"approved source path missing: {normalized}")
            continue
        if not candidate.is_file():
            errors.append(f"approved source path is not a file: {normalized}")
            continue
        existing_sources.append(normalized)
    return {
        "ok": not errors,
        "errors": errors,
        "existing_source_count": len(existing_sources),
        "existing_sources": existing_sources,
    }


def validate_live_revenue_evidence(evidence: dict[str, Any]) -> dict[str, Any]:
    missing = _missing(evidence, LIVE_REVENUE_EVIDENCE_REQUIRED_FIELDS)
    errors: list[str] = [f"missing required field: {field}" for field in missing]
    if evidence.get("type") != "ventureops-live-revenue-evidence":
        errors.append("type must be ventureops-live-revenue-evidence")
    if evidence.get("template_only") is True:
        errors.append("template_only revenue evidence cannot be used as live revenue proof")
    payment_status = str(evidence.get("payment_status") or "").strip().lower()
    if payment_status not in {"received", "settled"}:
        errors.append("payment_status must be received or settled")
    amount_value = 0.0
    try:
        amount_value = float(str(evidence.get("amount") or "0"))
    except ValueError:
        errors.append("amount must be numeric")
    if amount_value <= 0:
        errors.append("amount must be greater than zero")
    currency = str(evidence.get("currency") or "").strip().upper()
    if len(currency) != 3 or not currency.isalpha():
        errors.append("currency must be a 3-letter code")
    receipt_path = str(evidence.get("receipt_artifact_path") or "")
    if _is_unsafe_path(receipt_path):
        errors.append(f"receipt_artifact_path contains unsafe path: {receipt_path}")
    delivery_path = str(evidence.get("delivery_proof_path") or "")
    if _is_unsafe_path(delivery_path):
        errors.append(f"delivery_proof_path contains unsafe path: {delivery_path}")
    boundary = str(evidence.get("revenue_recognition_boundary") or "").strip().lower()
    if boundary != "proof_only_no_accounting_claim":
        errors.append("revenue_recognition_boundary must be proof_only_no_accounting_claim")
    if _contains_secret_key(evidence):
        errors.append("revenue evidence contains secret-shaped keys")
    return {
        "ok": not errors,
        "errors": errors,
        "amount": amount_value,
        "currency": currency,
        "receipt_artifact_path": receipt_path.replace("\\", "/").strip().lstrip("/"),
        "delivery_proof_path": delivery_path.replace("\\", "/").strip().lstrip("/"),
    }


def validate_live_client_scope_proof_artifact(artifact: dict[str, Any]) -> dict[str, Any]:
    missing = _missing(artifact, LIVE_CLIENT_SCOPE_PROOF_REQUIRED_FIELDS)
    errors: list[str] = [f"missing required field: {field}" for field in missing]
    if artifact.get("type") != "ventureops-live-client-scope-proof-gate":
        errors.append("type must be ventureops-live-client-scope-proof-gate")
    if artifact.get("workflow_id") != "agent_runtime_governance_audit":
        errors.append("workflow_id must be agent_runtime_governance_audit")
    if artifact.get("status") != "real_client_scope_evidence_validated_no_live_client_run":
        errors.append("status must be real_client_scope_evidence_validated_no_live_client_run")
    if str(artifact.get("approval_status") or "").strip().lower() != "approved":
        errors.append("approval_status must be approved")
    if artifact.get("approved_read_paths_validated") is not True:
        errors.append("approved_read_paths_validated must be true")
    if artifact.get("real_client_scope_present") is not True:
        errors.append("real_client_scope_present must be true")
    if artifact.get("real_client_scope_approved") is not True:
        errors.append("real_client_scope_approved must be true")
    if artifact.get("live_client_scope_proof_performed") is not False:
        errors.append("live_client_scope_proof_performed must remain false for proof-only revenue prerequisite")
    if artifact.get("live_client_data_ingested") is not False:
        errors.append("live_client_data_ingested must remain false for proof-only revenue prerequisite")
    if artifact.get("live_external_delivery_performed") is not False:
        errors.append("live_external_delivery_performed must remain false for proof-only revenue prerequisite")
    if str(artifact.get("delivery_boundary") or "").strip().lower() != "no_external_delivery":
        errors.append("delivery_boundary must be no_external_delivery")
    approved_read_paths = artifact.get("approved_read_paths")
    safe_read_paths: list[str] = []
    if not isinstance(approved_read_paths, list) or not approved_read_paths:
        errors.append("approved_read_paths must be a non-empty list")
    else:
        for raw_path in approved_read_paths:
            path = str(raw_path).replace("\\", "/").strip().lstrip("/")
            if _is_unsafe_path(str(raw_path)):
                errors.append(f"approved_read_paths contains unsafe path: {raw_path}")
            else:
                safe_read_paths.append(path)
    if _contains_secret_key(artifact):
        errors.append("live client proof artifact contains secret-shaped keys")
    return {
        "ok": not errors,
        "errors": errors,
        "client_approved_scope_id": str(artifact.get("client_approved_scope_id") or ""),
        "approved_read_path_count": len(safe_read_paths),
        "safe_read_paths": safe_read_paths,
    }


def validate_live_client_workflow_proof_artifact(artifact: dict[str, Any]) -> dict[str, Any]:
    missing = _missing(artifact, LIVE_CLIENT_WORKFLOW_PROOF_REQUIRED_FIELDS)
    errors: list[str] = [f"missing required field: {field}" for field in missing]
    if artifact.get("type") != "ventureops-live-client-workflow-proof":
        errors.append("type must be ventureops-live-client-workflow-proof")
    if artifact.get("status") != "live_client_workflow_proof_written":
        errors.append("status must be live_client_workflow_proof_written")
    if artifact.get("workflow_id") != "agent_runtime_governance_audit":
        errors.append("workflow_id must be agent_runtime_governance_audit")
    if str(artifact.get("approval_status") or "").strip().lower() != "approved":
        errors.append("approval_status must be approved")
    scope_packet_path = str(artifact.get("scope_packet_path") or "")
    if _is_unsafe_path(scope_packet_path):
        errors.append(f"scope_packet_path contains unsafe path: {scope_packet_path}")
    approved_read_paths = artifact.get("approved_read_paths")
    safe_read_paths: list[str] = []
    if not isinstance(approved_read_paths, list) or not approved_read_paths:
        errors.append("approved_read_paths must be a non-empty list")
    else:
        for raw_path in approved_read_paths:
            path = str(raw_path).replace("\\", "/").strip().lstrip("/")
            if _is_unsafe_path(str(raw_path)):
                errors.append(f"approved_read_paths contains unsafe path: {raw_path}")
            else:
                safe_read_paths.append(path)
    if artifact.get("approved_read_path_count") != len(safe_read_paths):
        errors.append("approved_read_path_count must match approved_read_paths")
    source_digests = artifact.get("source_digests")
    source_digest_paths: set[str] = set()
    source_digest_count = int(artifact.get("source_digest_count") or 0)
    if not isinstance(source_digests, list) or not source_digests:
        errors.append("source_digests must be a non-empty list")
    else:
        for item in source_digests:
            if not isinstance(item, dict):
                errors.append("source_digests entries must be objects")
                continue
            raw_path = str(item.get("path") or "")
            path = raw_path.replace("\\", "/").strip().lstrip("/")
            source_digest_paths.add(path)
            if _is_unsafe_path(raw_path):
                errors.append(f"source_digests contains unsafe path: {raw_path}")
            sha256 = str(item.get("sha256") or "")
            if len(sha256) != 64 or any(char not in "0123456789abcdef" for char in sha256):
                errors.append(f"source_digests sha256 must be 64 lowercase hex for path: {raw_path}")
            try:
                byte_count = int(item.get("byte_count") or 0)
            except (TypeError, ValueError):
                byte_count = 0
            if byte_count <= 0:
                errors.append(f"source_digests byte_count must be positive for path: {raw_path}")
    if source_digest_count != len(source_digests or []):
        errors.append("source_digest_count must match source_digests")
    if not set(safe_read_paths).issubset(source_digest_paths):
        errors.append("source_digests must cover approved_read_paths")
    if artifact.get("live_client_workflow_proof_performed") is not True:
        errors.append("live_client_workflow_proof_performed must be true")
    if artifact.get("scoped_client_data_ingested") is not True:
        errors.append("scoped_client_data_ingested must be true")
    if artifact.get("broad_client_data_ingested") is not False:
        errors.append("broad_client_data_ingested must be false")
    for field in (
        "live_external_delivery_performed",
        "external_send_performed",
        "crm_mutation_performed",
        "payment_mutation_performed",
        "revenue_claim_made",
    ):
        if artifact.get(field) is not False:
            errors.append(f"{field} must be false")
    for field in ("provider_calls", "browser_actions"):
        if int(artifact.get(field) or 0) != 0:
            errors.append(f"{field} must be 0")
    for field in ("scope_proof_gate_path", "client_report_path", "scorecard_path"):
        value = str(artifact.get(field) or "")
        if _is_unsafe_path(value):
            errors.append(f"{field} contains unsafe path: {value}")
    if _contains_secret_key(artifact):
        errors.append("live client workflow proof artifact contains secret-shaped keys")
    return {
        "ok": not errors,
        "errors": errors,
        "client_approved_scope_id": str(artifact.get("client_approved_scope_id") or ""),
        "approved_read_path_count": len(safe_read_paths),
        "safe_read_paths": safe_read_paths,
    }


def validate_live_revenue_proof_artifact(artifact: dict[str, Any]) -> dict[str, Any]:
    missing = _missing(artifact, LIVE_REVENUE_PROOF_REQUIRED_FIELDS)
    errors: list[str] = [f"missing required field: {field}" for field in missing]
    if artifact.get("type") != "ventureops-live-revenue-proof":
        errors.append("type must be ventureops-live-revenue-proof")
    if artifact.get("status") != "proof_only_recorded_no_accounting_claim":
        errors.append("status must be proof_only_recorded_no_accounting_claim")
    if artifact.get("workflow_id") != "agent_runtime_governance_audit":
        errors.append("workflow_id must be agent_runtime_governance_audit")
    payment_status = str(artifact.get("payment_status") or "").strip().lower()
    if payment_status not in {"received", "settled"}:
        errors.append("payment_status must be received or settled")
    amount_value = 0.0
    try:
        amount_value = float(str(artifact.get("amount") or "0"))
    except ValueError:
        errors.append("amount must be numeric")
    if amount_value <= 0:
        errors.append("amount must be greater than zero")
    currency = str(artifact.get("currency") or "").strip().upper()
    if len(currency) != 3 or not currency.isalpha():
        errors.append("currency must be a 3-letter code")
    for field in ("revenue_packet_path", "receipt_artifact_path", "delivery_proof_path", "live_client_proof_path"):
        value = str(artifact.get(field) or "")
        if _is_unsafe_path(value):
            errors.append(f"{field} contains unsafe path: {value}")
    for field in ("receipt_artifact_exists", "delivery_proof_exists", "live_client_proof_exists"):
        if artifact.get(field) is not True:
            errors.append(f"{field} must be true")
    if artifact.get("delivery_proof_artifact_valid") is not True:
        errors.append("delivery_proof_artifact_valid must be true")
    if artifact.get("live_client_proof_artifact_valid") is not True:
        errors.append("live_client_proof_artifact_valid must be true")
    if str(artifact.get("revenue_recognition_boundary") or "").strip().lower() != "proof_only_no_accounting_claim":
        errors.append("revenue_recognition_boundary must be proof_only_no_accounting_claim")
    for field in (
        "payment_mutation_performed",
        "crm_mutation_performed",
        "invoice_sent",
        "external_send_performed",
        "revenue_claim_made",
    ):
        if artifact.get(field) is not False:
            errors.append(f"{field} must be false")
    if _contains_secret_key(artifact):
        errors.append("live revenue proof artifact contains secret-shaped keys")
    return {
        "ok": not errors,
        "errors": errors,
        "revenue_proof_id": str(artifact.get("revenue_proof_id") or ""),
        "amount": amount_value,
        "currency": currency,
        "revenue_packet_path": str(artifact.get("revenue_packet_path") or "").replace("\\", "/").strip().lstrip("/"),
        "live_client_proof_path": str(artifact.get("live_client_proof_path") or "").replace("\\", "/").strip().lstrip("/"),
    }


def validate_live_delivery_proof_artifact(artifact: dict[str, Any]) -> dict[str, Any]:
    missing = _missing(artifact, LIVE_DELIVERY_PROOF_REQUIRED_FIELDS)
    errors: list[str] = [f"missing required field: {field}" for field in missing]
    if artifact.get("type") != "ventureops-live-delivery-proof":
        errors.append("type must be ventureops-live-delivery-proof")
    if artifact.get("status") != "operator_attested_delivery_recorded":
        errors.append("status must be operator_attested_delivery_recorded")
    if artifact.get("workflow_id") != "agent_runtime_governance_audit":
        errors.append("workflow_id must be agent_runtime_governance_audit")
    delivery_status = str(artifact.get("delivery_status") or "").strip().lower()
    if delivery_status not in {"delivered", "accepted"}:
        errors.append("delivery_status must be delivered or accepted")
    if str(artifact.get("delivery_boundary") or "").strip().lower() != "operator_attested_delivery_no_chaseos_external_send":
        errors.append("delivery_boundary must be operator_attested_delivery_no_chaseos_external_send")
    for field in ("client_safe_delivery_artifact_path", "live_client_proof_path"):
        value = str(artifact.get(field) or "")
        if _is_unsafe_path(value):
            errors.append(f"{field} contains unsafe path: {value}")
    if artifact.get("operator_attested_delivery_performed") is not True:
        errors.append("operator_attested_delivery_performed must be true")
    for field in (
        "external_send_performed_by_chaseos",
        "crm_mutation_performed",
        "payment_mutation_performed",
        "invoice_sent",
        "revenue_claim_made",
    ):
        if artifact.get(field) is not False:
            errors.append(f"{field} must be false")
    for field in ("provider_calls", "browser_actions"):
        if int(artifact.get(field) or 0) != 0:
            errors.append(f"{field} must be 0")
    if _contains_secret_key(artifact):
        errors.append("live delivery proof artifact contains secret-shaped keys")
    return {
        "ok": not errors,
        "errors": errors,
        "delivery_proof_id": str(artifact.get("delivery_proof_id") or ""),
        "delivery_status": delivery_status,
        "live_client_proof_path": str(artifact.get("live_client_proof_path") or "").replace("\\", "/").strip().lstrip("/"),
    }


def validate_client_safe_delivery_artifact(artifact: dict[str, Any]) -> dict[str, Any]:
    missing = _missing(artifact, CLIENT_SAFE_DELIVERY_ARTIFACT_REQUIRED_FIELDS)
    errors: list[str] = [f"missing required field: {field}" for field in missing]
    if artifact.get("type") != "ventureops-client-safe-delivery-artifact":
        errors.append("type must be ventureops-client-safe-delivery-artifact")
    if artifact.get("workflow_id") != "agent_runtime_governance_audit":
        errors.append("workflow_id must be agent_runtime_governance_audit")
    if artifact.get("redacted") is not True:
        errors.append("redacted must be true")
    if artifact.get("client_safe") is not True:
        errors.append("client_safe must be true")
    if not str(artifact.get("delivery_summary") or "").strip():
        errors.append("delivery_summary must be non-empty")
    source_path = str(artifact.get("source_live_client_proof_path") or "")
    if _is_unsafe_path(source_path):
        errors.append(f"source_live_client_proof_path contains unsafe path: {source_path}")
    for field in (
        "external_send_performed_by_chaseos",
        "crm_mutation_performed",
        "payment_mutation_performed",
        "invoice_sent",
        "revenue_claim_made",
    ):
        if artifact.get(field) is not False:
            errors.append(f"{field} must be false")
    for field in ("provider_calls", "browser_actions"):
        try:
            count = int(artifact.get(field) or 0)
        except (TypeError, ValueError):
            count = -1
        if count != 0:
            errors.append(f"{field} must be 0")
    if _contains_secret_key(artifact):
        errors.append("client-safe delivery artifact contains secret-shaped keys")
    return {
        "ok": not errors,
        "errors": errors,
        "workflow_id": str(artifact.get("workflow_id") or ""),
        "client_label": str(artifact.get("client_label") or ""),
        "delivery_reference_id": str(artifact.get("delivery_reference_id") or ""),
        "source_live_client_proof_path": source_path.replace("\\", "/").strip().lstrip("/"),
    }


def _scan_json_artifacts(root: Path, relative_root: str) -> list[tuple[str, dict[str, Any]]]:
    scan_root = root / relative_root
    if not scan_root.exists() or not scan_root.is_dir():
        return []
    artifacts: list[tuple[str, dict[str, Any]]] = []
    for path in sorted(scan_root.rglob("*.json")):
        if not path.is_file():
            continue
        try:
            relative = str(path.resolve().relative_to(root)).replace("\\", "/")
        except ValueError:
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(data, dict):
            artifacts.append((relative, data))
    return artifacts


def _normalized_artifact_reference(artifact: dict[str, Any], field: str) -> str:
    return str(artifact.get(field) or "").replace("\\", "/").strip().lstrip("/")


def _normalized_path_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).replace("\\", "/").strip().lstrip("/") for item in value]


def _validate_live_client_workflow_reference_artifacts(root: Path, artifact: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    scope_packet_path = _normalized_artifact_reference(artifact, "scope_packet_path")
    scope_proof_gate_path = _normalized_artifact_reference(artifact, "scope_proof_gate_path")
    client_report_path = _normalized_artifact_reference(artifact, "client_report_path")
    scorecard_path = _normalized_artifact_reference(artifact, "scorecard_path")
    workflow_scope_id = str(artifact.get("client_approved_scope_id") or "")
    workflow_client_label = str(artifact.get("client_label") or "")
    workflow_approval_id = str(artifact.get("approval_id") or "")
    workflow_run_id = str(artifact.get("run_id") or "")
    workflow_id = str(artifact.get("workflow_id") or "")
    workflow_read_paths = set(_normalized_path_list(artifact.get("approved_read_paths")))

    scope_packet_target = root / scope_packet_path
    if not scope_packet_target.is_file():
        errors.append(f"scope packet artifact missing: {scope_packet_path}")
    else:
        try:
            scope_packet_data = json.loads(scope_packet_target.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"scope packet artifact unreadable: {scope_packet_path}: {exc}")
        else:
            if not isinstance(scope_packet_data, dict):
                errors.append(f"scope packet artifact is not a JSON object: {scope_packet_path}")
            else:
                scope_packet_validation = validate_real_client_scope_evidence(scope_packet_data)
                if not scope_packet_validation["ok"]:
                    errors.extend(
                        [f"scope packet artifact invalid: {error}" for error in scope_packet_validation["errors"]]
                    )
                else:
                    approval_validation = validate_scope_evidence_approval_artifact(root, scope_packet_data)
                    if not approval_validation["ok"]:
                        errors.extend(
                            [
                                f"scope packet approval artifact invalid: {error}"
                                for error in approval_validation["errors"]
                            ]
                        )
                    source_validation = validate_scope_evidence_source_paths(
                        root, scope_packet_validation["safe_read_paths"]
                    )
                    if not source_validation["ok"]:
                        errors.extend(
                            [f"scope packet source path invalid: {error}" for error in source_validation["errors"]]
                        )
                    if str(scope_packet_data.get("client_approved_scope_id") or "") != workflow_scope_id:
                        errors.append("scope packet client_approved_scope_id does not match live-client workflow proof")
                    if str(scope_packet_data.get("client_label") or "") != workflow_client_label:
                        errors.append("scope packet client_label does not match live-client workflow proof")
                    if str(scope_packet_data.get("approval_id") or "") != workflow_approval_id:
                        errors.append("scope packet approval_id does not match live-client workflow proof")
                    if set(scope_packet_validation["safe_read_paths"]) != workflow_read_paths:
                        errors.append("scope packet approved_read_paths do not match live-client workflow proof")

    scope_target = root / scope_proof_gate_path
    if not scope_target.is_file():
        errors.append(f"scope proof gate artifact missing: {scope_proof_gate_path}")
    else:
        try:
            scope_data = json.loads(scope_target.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"scope proof gate artifact unreadable: {scope_proof_gate_path}: {exc}")
        else:
            if not isinstance(scope_data, dict):
                errors.append(f"scope proof gate artifact is not a JSON object: {scope_proof_gate_path}")
            else:
                scope_validation = validate_live_client_scope_proof_artifact(scope_data)
                if not scope_validation["ok"]:
                    errors.extend(
                        [f"scope proof gate artifact invalid: {error}" for error in scope_validation["errors"]]
                    )
                else:
                    if str(scope_data.get("client_approved_scope_id") or "") != workflow_scope_id:
                        errors.append("scope proof gate client_approved_scope_id does not match live-client workflow proof")
                    if str(scope_data.get("client_label") or "") != workflow_client_label:
                        errors.append("scope proof gate client_label does not match live-client workflow proof")
                    if str(scope_data.get("approval_id") or "") != workflow_approval_id:
                        errors.append("scope proof gate approval_id does not match live-client workflow proof")
                    if set(scope_validation["safe_read_paths"]) != workflow_read_paths:
                        errors.append("scope proof gate approved_read_paths do not match live-client workflow proof")

    if not (root / client_report_path).is_file():
        errors.append(f"client report artifact missing: {client_report_path}")

    scorecard_target = root / scorecard_path
    if not scorecard_target.is_file():
        errors.append(f"scorecard artifact missing: {scorecard_path}")
    else:
        try:
            scorecard_data = json.loads(scorecard_target.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"scorecard artifact unreadable: {scorecard_path}: {exc}")
        else:
            if not isinstance(scorecard_data, dict):
                errors.append(f"scorecard artifact is not a JSON object: {scorecard_path}")
            else:
                scorecard_validation = validate_agent_scorecard(scorecard_data)
                if not scorecard_validation["ok"]:
                    errors.extend([f"scorecard artifact invalid: {error}" for error in scorecard_validation["errors"]])
                else:
                    if str(scorecard_data.get("workflow_id") or "") != workflow_id:
                        errors.append("scorecard workflow_id does not match live-client workflow proof")
                    if str(scorecard_data.get("run_id") or "") != workflow_run_id:
                        errors.append("scorecard run_id does not match live-client workflow proof")

    return errors


def _validate_redacted_receipt_artifact(artifact: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    if artifact.get("redacted") is not True:
        errors.append("redacted must be true")
    if _contains_secret_key(artifact):
        errors.append("receipt artifact contains secret-shaped keys")
    return {"ok": not errors, "errors": errors}


def _validate_live_revenue_packet_reference_artifact(root: Path, artifact: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    revenue_packet_path = _normalized_artifact_reference(artifact, "revenue_packet_path")
    target = root / revenue_packet_path
    if not target.is_file():
        return [f"revenue packet artifact missing: {revenue_packet_path}"]
    try:
        revenue_packet = json.loads(target.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"revenue packet artifact unreadable: {revenue_packet_path}: {exc}"]
    if not isinstance(revenue_packet, dict):
        return [f"revenue packet artifact is not a JSON object: {revenue_packet_path}"]

    validation = validate_live_revenue_evidence(revenue_packet)
    if not validation["ok"]:
        errors.extend([f"revenue packet artifact invalid: {error}" for error in validation["errors"]])
        return errors

    for field in ("revenue_proof_id", "workflow_id", "client_label", "payment_reference_id", "crm_reference_id", "approval_id"):
        if str(revenue_packet.get(field) or "") != str(artifact.get(field) or ""):
            errors.append(f"revenue packet {field} does not match revenue proof")
    if str(revenue_packet.get("payment_status") or "").strip().lower() != str(artifact.get("payment_status") or "").strip().lower():
        errors.append("revenue packet payment_status does not match revenue proof")
    if validation["amount"] != float(str(artifact.get("amount") or "0")):
        errors.append("revenue packet amount does not match revenue proof")
    if validation["currency"] != str(artifact.get("currency") or "").strip().upper():
        errors.append("revenue packet currency does not match revenue proof")
    for field in ("receipt_artifact_path", "delivery_proof_path"):
        if _normalized_artifact_reference(revenue_packet, field) != _normalized_artifact_reference(artifact, field):
            errors.append(f"revenue packet {field} does not match revenue proof")
    return errors


def discover_external_completion_artifacts(vault_root: str | Path) -> dict[str, Any]:
    root = Path(vault_root).resolve()
    valid_live_client_workflow_proofs: list[str] = []
    valid_live_client_workflow_proof_artifacts: dict[str, dict[str, Any]] = {}
    invalid_live_client_workflow_proofs: list[dict[str, Any]] = []
    for relative, artifact in _scan_json_artifacts(root, "07_LOGS/Workflow-Proofs"):
        if artifact.get("type") != "ventureops-live-client-workflow-proof":
            continue
        validation = validate_live_client_workflow_proof_artifact(artifact)
        if validation["ok"]:
            reference_errors = _validate_live_client_workflow_reference_artifacts(root, artifact)
            if not reference_errors:
                valid_live_client_workflow_proofs.append(relative)
                valid_live_client_workflow_proof_artifacts[relative] = artifact
            else:
                invalid_live_client_workflow_proofs.append({"path": relative, "errors": reference_errors})
        else:
            invalid_live_client_workflow_proofs.append({"path": relative, "errors": validation["errors"]})

    valid_live_revenue_proofs: list[str] = []
    invalid_live_revenue_proofs: list[dict[str, Any]] = []
    for relative, artifact in _scan_json_artifacts(root, "07_LOGS/Revenue-Proofs"):
        if artifact.get("type") != "ventureops-live-revenue-proof":
            continue
        validation = validate_live_revenue_proof_artifact(artifact)
        if validation["ok"]:
            reference_errors: list[str] = _validate_live_revenue_packet_reference_artifact(root, artifact)
            live_client_path = validation["live_client_proof_path"]
            if live_client_path in valid_live_client_workflow_proofs:
                revenue_workflow_id = str(artifact.get("workflow_id") or "")
                revenue_client_label = str(artifact.get("client_label") or "")
                live_client_artifact = valid_live_client_workflow_proof_artifacts[live_client_path]
                if str(live_client_artifact.get("workflow_id") or "") != revenue_workflow_id:
                    reference_errors.append("live-client proof workflow_id does not match revenue proof")
                if str(live_client_artifact.get("client_label") or "") != revenue_client_label:
                    reference_errors.append("live-client proof client_label does not match revenue proof")
                receipt_path = _normalized_artifact_reference(artifact, "receipt_artifact_path")
                delivery_path = _normalized_artifact_reference(artifact, "delivery_proof_path")
                if not (root / receipt_path).is_file():
                    reference_errors.append(f"receipt artifact missing: {receipt_path}")
                else:
                    try:
                        receipt_data = json.loads((root / receipt_path).read_text(encoding="utf-8"))
                    except Exception as exc:
                        reference_errors.append(f"receipt artifact unreadable: {receipt_path}: {exc}")
                    else:
                        if not isinstance(receipt_data, dict):
                            reference_errors.append(f"receipt artifact is not a JSON object: {receipt_path}")
                        else:
                            receipt_validation = _validate_redacted_receipt_artifact(receipt_data)
                            if not receipt_validation["ok"]:
                                reference_errors.extend(
                                    [f"receipt artifact invalid: {error}" for error in receipt_validation["errors"]]
                                )
                if not (root / delivery_path).is_file():
                    reference_errors.append(f"delivery proof artifact missing: {delivery_path}")
                else:
                    try:
                        delivery_data = json.loads((root / delivery_path).read_text(encoding="utf-8"))
                    except Exception as exc:
                        reference_errors.append(f"delivery proof artifact unreadable: {delivery_path}: {exc}")
                    else:
                        if not isinstance(delivery_data, dict):
                            reference_errors.append(f"delivery proof artifact is not a JSON object: {delivery_path}")
                        else:
                            delivery_validation = validate_live_delivery_proof_artifact(delivery_data)
                            if delivery_validation["ok"]:
                                if str(delivery_data.get("workflow_id") or "") != revenue_workflow_id:
                                    reference_errors.append("delivery proof workflow_id does not match revenue proof")
                                if str(delivery_data.get("client_label") or "") != revenue_client_label:
                                    reference_errors.append("delivery proof client_label does not match revenue proof")
                                if delivery_validation["live_client_proof_path"] != live_client_path:
                                    reference_errors.append(
                                        "delivery proof live_client_proof_path does not match revenue proof live_client_proof_path"
                                    )
                                client_safe_delivery_path = _normalized_artifact_reference(
                                    delivery_data, "client_safe_delivery_artifact_path"
                                )
                                if not (root / client_safe_delivery_path).is_file():
                                    reference_errors.append(
                                        f"client-safe delivery artifact missing: {client_safe_delivery_path}"
                                    )
                                else:
                                    try:
                                        client_safe_delivery_data = json.loads(
                                            (root / client_safe_delivery_path).read_text(encoding="utf-8")
                                        )
                                    except Exception as exc:
                                        reference_errors.append(
                                            f"client-safe delivery artifact unreadable: {client_safe_delivery_path}: {exc}"
                                        )
                                    else:
                                        if not isinstance(client_safe_delivery_data, dict):
                                            reference_errors.append(
                                                f"client-safe delivery artifact is not a JSON object: {client_safe_delivery_path}"
                                            )
                                        else:
                                            client_safe_delivery_validation = validate_client_safe_delivery_artifact(
                                                client_safe_delivery_data
                                            )
                                            if not client_safe_delivery_validation["ok"]:
                                                reference_errors.extend(
                                                    [
                                                        f"client-safe delivery artifact invalid: {error}"
                                                        for error in client_safe_delivery_validation["errors"]
                                                    ]
                                                )
                                            else:
                                                if client_safe_delivery_validation["workflow_id"] != revenue_workflow_id:
                                                    reference_errors.append(
                                                        "client-safe delivery artifact workflow_id does not match revenue proof"
                                                    )
                                                if client_safe_delivery_validation["client_label"] != revenue_client_label:
                                                    reference_errors.append(
                                                        "client-safe delivery artifact client_label does not match revenue proof"
                                                    )
                                                if (
                                                    client_safe_delivery_validation["delivery_reference_id"]
                                                    != str(delivery_data.get("delivery_reference_id") or "")
                                                ):
                                                    reference_errors.append(
                                                        "client-safe delivery artifact delivery_reference_id does not match delivery proof"
                                                    )
                                                if client_safe_delivery_validation["source_live_client_proof_path"] != live_client_path:
                                                    reference_errors.append(
                                                        "client-safe delivery artifact source_live_client_proof_path does not match revenue proof live_client_proof_path"
                                                    )
                            else:
                                reference_errors.extend(
                                    [f"delivery proof artifact invalid: {error}" for error in delivery_validation["errors"]]
                                )
            else:
                reference_errors.append(f"referenced live client proof is not valid or not discovered: {live_client_path}")
            if not reference_errors:
                valid_live_revenue_proofs.append(relative)
            else:
                invalid_live_revenue_proofs.append(
                    {
                        "path": relative,
                        "errors": reference_errors,
                    }
                )
        else:
            invalid_live_revenue_proofs.append({"path": relative, "errors": validation["errors"]})

    return {
        "live_client_workflow_proof_present": bool(valid_live_client_workflow_proofs),
        "live_revenue_workflow_proof_present": bool(valid_live_revenue_proofs),
        "valid_live_client_workflow_proof_artifacts": valid_live_client_workflow_proofs,
        "valid_live_revenue_proof_artifacts": valid_live_revenue_proofs,
        "invalid_live_client_workflow_proof_artifacts": invalid_live_client_workflow_proofs,
        "invalid_live_revenue_proof_artifacts": invalid_live_revenue_proofs,
    }


def discover_final_evidence_bundle_validation_reports(
    vault_root: str | Path,
    external_completion_artifacts: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Find ready final bundle validation reports that match current final proof artifacts."""
    root = Path(vault_root).resolve()
    external_completion = external_completion_artifacts or discover_external_completion_artifacts(root)
    valid_live_client_paths = set(external_completion.get("valid_live_client_workflow_proof_artifacts") or [])
    valid_revenue_paths = set(external_completion.get("valid_live_revenue_proof_artifacts") or [])
    valid_reports: list[str] = []
    invalid_reports: list[dict[str, Any]] = []

    for relative, artifact in _scan_json_artifacts(root, "07_LOGS/Workflow-Proofs"):
        if "ready_for_completion_audit" not in artifact and artifact.get("validation_status") != "ready_for_completion_audit":
            continue

        errors: list[str] = []
        if artifact.get("ready_for_completion_audit") is not True:
            errors.append("ready_for_completion_audit must be true")
        if artifact.get("validation_status") != "ready_for_completion_audit":
            errors.append("validation_status must be ready_for_completion_audit")
        blockers = artifact.get("blockers")
        if blockers not in (None, []):
            errors.append("blockers must be empty")

        bundle_path = str(artifact.get("bundle_path") or "").replace("\\", "/").strip().lstrip("/")
        if not bundle_path:
            errors.append("bundle_path must be present")
        else:
            from runtime.ventureops.final_external_evidence_bundle import validate_final_external_evidence_bundle

            bundle_validation = validate_final_external_evidence_bundle(root, bundle_path=bundle_path)
            if bundle_validation.get("ready_for_completion_audit") is not True:
                current_blockers = bundle_validation.get("blockers") or ["ready_for_completion_audit must be true"]
                errors.extend([f"report bundle_path is not currently valid: {error}" for error in current_blockers])

        bundle_fields = artifact.get("bundle_fields")
        if not isinstance(bundle_fields, dict):
            errors.append("bundle_fields must be an object")
            bundle_fields = {}

        live_client_path = str(bundle_fields.get("live_client_workflow_proof_path") or "").replace("\\", "/")
        live_revenue_path = str(bundle_fields.get("live_revenue_proof_path") or "").replace("\\", "/")
        if live_client_path not in valid_live_client_paths:
            errors.append("bundle live-client workflow proof is not currently valid")
        if live_revenue_path not in valid_revenue_paths:
            errors.append("bundle live revenue proof is not currently valid")

        required_valid_flags = (
            "scope_evidence_valid",
            "scope_approval_artifact_valid",
            "scope_sources_valid",
            "live_client_workflow_proof_valid",
            "delivery_proof_artifact_valid",
            "client_safe_delivery_artifact_valid",
            "revenue_evidence_valid",
            "live_revenue_proof_valid",
        )
        for field in required_valid_flags:
            if artifact.get(field) is not True:
                errors.append(f"{field} must be true")

        if errors:
            invalid_reports.append({"path": relative, "errors": errors})
        else:
            valid_reports.append(relative)

    return {
        "final_evidence_bundle_validation_report_present": bool(valid_reports),
        "final_evidence_bundle_validation_ready": bool(valid_reports),
        "valid_final_evidence_bundle_validation_reports": valid_reports,
        "invalid_final_evidence_bundle_validation_reports": invalid_reports,
    }


def validate_proof_card(card: dict[str, Any]) -> dict[str, Any]:
    missing = _missing(card, PROOF_CARD_REQUIRED_FIELDS)
    errors = [f"missing required field: {field}" for field in missing]
    if _contains_secret_key(card):
        errors.append("proof card contains secret-shaped keys")
    if not isinstance(card.get("input_sources", []), list):
        errors.append("input_sources must be a list")
    if not isinstance(card.get("files_written", []), list):
        errors.append("files_written must be a list")
    if errors:
        raise ValueError("; ".join(errors))
    return {"ok": True, "errors": []}


def validate_agent_scorecard(scorecard: dict[str, Any]) -> dict[str, Any]:
    missing = _missing(scorecard, SCORECARD_REQUIRED_FIELDS)
    errors = [f"missing required field: {field}" for field in missing]
    status = str(scorecard.get("status") or "")
    if status not in {"untested", "dry_run_passed", "internal_run_passed", "client_ready", "monetized", "blocked", "retired"}:
        errors.append(f"invalid scorecard status: {status}")
    return {"ok": not errors, "errors": errors}


def validate_recommendation(recommendation: dict[str, Any]) -> dict[str, Any]:
    missing = _missing(recommendation, RECOMMENDATION_REQUIRED_FIELDS)
    errors = [f"missing required field: {field}" for field in missing]
    evidence = recommendation.get("evidence_files")
    if not isinstance(evidence, list) or not evidence:
        errors.append("recommendation must include at least one evidence file")
    confidence = recommendation.get("confidence_score")
    if not isinstance(confidence, (int, float)) or not 0 <= float(confidence) <= 1:
        errors.append("confidence_score must be between 0 and 1")
    if str(recommendation.get("workflow_id")) == "tradesync_strikezone_supply_engine":
        approvals = " ".join(str(item).lower() for item in recommendation.get("approval_requirements") or [])
        risks = " ".join(str(item).lower() for item in recommendation.get("risks") or [])
        if "live trading" not in risks or "human approval" not in approvals:
            errors.append("crypto/trading recommendations must preserve live-trading approval boundary")
    return {"ok": not errors, "errors": errors}


def validate_registry(vault_root: str | Path | None = None) -> dict[str, Any]:
    registry = load_use_case_registry(vault_root)
    records = workflow_records(registry)
    ids = {str(record.get("workflow_id")) for record in records}
    errors: list[str] = []
    for workflow_id in REQUIRED_WORKFLOW_IDS:
        if workflow_id not in ids:
            errors.append(f"missing workflow_id: {workflow_id}")
    for record in records:
        for field in ("workflow_id", "name", "type", "purpose", "status", "required_runtime_surfaces", "approval_requirements", "proof_artifact"):
            if field not in record:
                errors.append(f"{record.get('workflow_id', '<unknown>')} missing {field}")
        if record.get("workflow_id") == "tradesync_strikezone_supply_engine":
            if not record.get("optional_domain_pack"):
                errors.append("crypto/trading workflow must be optional_domain_pack")
            if record.get("default_recommendation") is not False:
                errors.append("crypto/trading workflow must not be a default recommendation")
    return {"ok": not errors, "errors": errors, "workflow_count": len(records)}


def validate_schema_templates(vault_root: str | Path | None = None) -> dict[str, Any]:
    root = Path(vault_root).resolve() if vault_root is not None else Path(__file__).resolve().parents[2]
    templates_dir = root / "runtime" / "workflows" / "registry" / "templates"
    required = {
        "workflow_pack_schema.yaml": WORKFLOW_PACK_REQUIRED_FIELDS,
        "proof_card_schema.yaml": PROOF_CARD_REQUIRED_FIELDS,
        "agent_scorecard_schema.yaml": SCORECARD_REQUIRED_FIELDS,
        "workflow_recommendation_schema.yaml": RECOMMENDATION_REQUIRED_FIELDS,
        "domain_playbook_schema.yaml": {
            "domain_id",
            "name",
            "target_users",
            "evidence_sources",
            "workflow_opportunities",
            "approval_boundaries",
            "proof_artifacts",
            "monetization_paths",
            "risks",
        },
        "real_client_scope_approval_schema.yaml": REAL_CLIENT_SCOPE_APPROVAL_REQUIRED_FIELDS,
        "real_client_scope_evidence_schema.yaml": REAL_CLIENT_SCOPE_EVIDENCE_REQUIRED_FIELDS,
        "live_revenue_evidence_schema.yaml": LIVE_REVENUE_EVIDENCE_REQUIRED_FIELDS,
    }
    mission_templates_dir = root / "runtime" / "ventureops" / "templates"
    mission_required = {
        "mission_manifest_schema.yaml": MISSION_MANIFEST_REQUIRED_FIELDS,
        "mission_state_schema.yaml": MISSION_STATE_REQUIRED_FIELDS,
        "workflow_evolution_proposal_schema.yaml": WORKFLOW_EVOLUTION_PROPOSAL_REQUIRED_FIELDS,
        "domain_goal_profile_schema.yaml": DOMAIN_GOAL_PROFILE_REQUIRED_FIELDS,
        "sub_agent_plan_schema.yaml": SUB_AGENT_PLAN_REQUIRED_FIELDS | SUB_AGENT_REQUIRED_FIELDS,
        "site_profile_schema.yaml": SITE_PROFILE_REQUIRED_FIELDS,
        "mission_review_schema.yaml": MISSION_REVIEW_REQUIRED_FIELDS,
        "mission_recommendation_schema.yaml": MISSION_RECOMMENDATION_REQUIRED_FIELDS,
        "mission_activation_approval_consumption_schema.yaml": MISSION_ACTIVATION_APPROVAL_CONSUMPTION_REQUIRED_FIELDS,
        "mission_manifest_promotion_review_schema.yaml": MISSION_MANIFEST_PROMOTION_REVIEW_REQUIRED_FIELDS,
        "mission_agent_bus_enqueue_gate_schema.yaml": MISSION_AGENT_BUS_ENQUEUE_REQUIRED_FIELDS,
    }
    errors: list[str] = []
    for filename, fields in required.items():
        path = templates_dir / filename
        if not path.exists():
            errors.append(f"missing schema template: {filename}")
            continue
        data = _load_yaml_file(path)
        declared = set(str(item) for item in data.get("required_fields") or [])
        missing = sorted(fields - declared)
        if missing:
            errors.append(f"{filename} missing required fields: {missing}")
    for filename, fields in mission_required.items():
        path = mission_templates_dir / filename
        if not path.exists():
            errors.append(f"missing mission schema template: {filename}")
            continue
        data = _load_yaml_file(path)
        declared = set(str(item) for item in data.get("required_fields") or [])
        missing = sorted(fields - declared)
        if missing:
            errors.append(f"{filename} missing required fields: {missing}")
    return {"ok": not errors, "errors": errors}


def audit_external_readiness_completion(vault_root: str | Path | None = None) -> dict[str, Any]:
    """Audit VentureOps external readiness against the real repo artifacts.

    This audit intentionally separates "valid current partial state" from
    "complete". It should return ok=True when the passover/handover and proof
    chain are internally coherent, while still returning complete=False until
    live client and live revenue evidence exists.
    """

    root = Path(vault_root).resolve() if vault_root is not None else Path(__file__).resolve().parents[2]
    passover_rel = Path("06_AGENTS/VentureOps-External-Readiness-Passover.md")
    handover_rel = Path("06_AGENTS/VentureOps-External-Readiness-Handover.md")
    requested_handover_rel = Path("06_AGENTS/VentureOps-externaal-Readiness-Handover.md")
    passover_path = root / passover_rel
    handover_path = root / handover_rel
    requested_handover_path = root / requested_handover_rel
    scope_schema_rel = "runtime/workflows/registry/templates/real_client_scope_evidence_schema.yaml"
    scope_approval_schema_rel = "runtime/workflows/registry/templates/real_client_scope_approval_schema.yaml"
    scope_approval_template_rel = "05_TEMPLATES/Real-Client-Scope-Approval-Template.md"
    scope_template_rel = "05_TEMPLATES/Real-Client-Scope-Evidence-Template.md"
    revenue_schema_rel = "runtime/workflows/registry/templates/live_revenue_evidence_schema.yaml"
    revenue_template_rel = "05_TEMPLATES/Live-Revenue-Evidence-Template.md"
    readiness_module_rel = "runtime/ventureops/live_client_readiness.py"
    evidence_intake_module_rel = "runtime/ventureops/evidence_intake.py"
    evidence_discovery_preflight_module_rel = "runtime/ventureops/evidence_discovery_preflight.py"
    real_client_input_manifest_module_rel = "runtime/ventureops/real_client_input_manifest.py"
    scope_approval_packet_builder_module_rel = "runtime/ventureops/scope_approval_packet_builder.py"
    scope_evidence_packet_builder_module_rel = "runtime/ventureops/scope_evidence_packet_builder.py"
    revenue_evidence_packet_builder_module_rel = "runtime/ventureops/revenue_evidence_packet_builder.py"
    delivery_proof_packet_builder_module_rel = "runtime/ventureops/delivery_proof_packet_builder.py"
    feature_family_completion_audit_module_rel = "runtime/ventureops/feature_family_completion_audit.py"
    final_external_execution_runbook_module_rel = "runtime/ventureops/final_external_execution_runbook.py"
    final_external_evidence_bundle_module_rel = "runtime/ventureops/final_external_evidence_bundle.py"
    final_evidence_bundle_packet_builder_module_rel = "runtime/ventureops/final_evidence_bundle_packet_builder.py"
    real_evidence_closeout_module_rel = "runtime/ventureops/real_evidence_closeout_readiness.py"
    live_client_scope_proof_module_rel = "runtime/ventureops/live_client_scope_proof.py"
    live_client_workflow_proof_module_rel = "runtime/ventureops/live_client_workflow_proof.py"
    live_revenue_proof_module_rel = "runtime/ventureops/live_revenue_proof.py"
    revenue_readiness_module_rel = "runtime/ventureops/live_revenue_readiness.py"
    readiness_cli_rel = "runtime/cli/ventureops_commands.py"
    command_contract_rel = "runtime/cli/command_contract.json"
    live_client_readiness_report_rel = (
        "07_LOGS/Workflow-Proofs/2026-05-12_ventureops-live-client-proof-readiness-report.json"
    )
    live_revenue_readiness_report_rel = (
        "07_LOGS/Workflow-Proofs/2026-05-12_ventureops-live-revenue-proof-readiness-report.json"
    )
    scope_evidence_template_report_rel = (
        "07_LOGS/Workflow-Proofs/2026-05-11_ventureops-scope-evidence-template.json"
    )
    revenue_evidence_template_report_rel = (
        "07_LOGS/Workflow-Proofs/2026-05-11_ventureops-revenue-evidence-template.json"
    )
    passover = _read_text_if_exists(passover_path)
    handover = _read_text_if_exists(handover_path)
    requested_handover = _read_text_if_exists(requested_handover_path)
    command_contract = _read_text_if_exists(root / command_contract_rel)
    cli_text = _read_text_if_exists(root / readiness_cli_rel)
    test_text = _read_text_if_exists(root / "runtime/ventureops/test_ventureops.py")
    validation_text = _read_text_if_exists(root / "runtime/ventureops/validation.py")
    final_external_execution_runbook_text = _read_text_if_exists(root / final_external_execution_runbook_module_rel)

    expected_artifacts = [LIVE_CLIENT_SCOPE_PREFIX + suffix for suffix in LIVE_CLIENT_SCOPE_EXPECTED_SUFFIXES]
    existing_artifacts = [path for path in expected_artifacts if (root / path).exists()]
    scorecard_path = root / f"{LIVE_CLIENT_SCOPE_PREFIX}_scorecard.json"
    contract_path = root / f"{LIVE_CLIENT_SCOPE_PREFIX}_live-client-scope-contract.json"
    scorecard = _load_json_if_exists(scorecard_path)
    contract = _load_json_if_exists(contract_path)
    live_client_readiness_report = _load_json_if_exists(root / live_client_readiness_report_rel)
    live_revenue_readiness_report = _load_json_if_exists(root / live_revenue_readiness_report_rel)
    scope_evidence_template_report = _load_json_if_exists(root / scope_evidence_template_report_rel)
    revenue_evidence_template_report = _load_json_if_exists(root / revenue_evidence_template_report_rel)
    external_completion_artifacts = discover_external_completion_artifacts(root)
    final_bundle_validation_reports = discover_final_evidence_bundle_validation_reports(
        root,
        external_completion_artifacts,
    )
    external_completion_artifact_discovery_valid = isinstance(external_completion_artifacts, dict) and all(
        key in external_completion_artifacts
        for key in (
            "live_client_workflow_proof_present",
            "live_revenue_workflow_proof_present",
            "valid_live_client_workflow_proof_artifacts",
            "valid_live_revenue_proof_artifacts",
            "invalid_live_client_workflow_proof_artifacts",
            "invalid_live_revenue_proof_artifacts",
        )
    )
    metrics = scorecard.get("metrics") if isinstance(scorecard.get("metrics"), dict) else {}

    handover_alias_valid = (
        handover_path.exists()
        and str(passover_rel).replace("\\", "/") in handover
        and _contains_external_readiness_status(handover)
        and "live-client-workflow-proof" in handover
        and "live-revenue-proof-readiness --revenue-packet PATH --live-client-proof-path PATH --json" in handover
    )
    requested_handover_alias_valid = (
        requested_handover_path.exists()
        and str(handover_rel).replace("\\", "/") in requested_handover
        and str(passover_rel).replace("\\", "/") in requested_handover
        and _contains_external_readiness_status(requested_handover)
        and "live-client-scope-proof" in requested_handover
        and "live-revenue-proof" in requested_handover
    )
    requested_handover_next_pass_valid = (
        requested_handover_path.exists()
        and "Next required real-use pass: `ventureops-live-revenue-proof`" in requested_handover
        and "live-revenue-proof-readiness --revenue-packet PATH --live-client-proof-path PATH --json"
        in requested_handover
        and "live-revenue-proof --revenue-packet PATH --live-client-proof-path PATH --execute-proof --json"
        in requested_handover
        and "live-client-workflow-proof --scope-packet PATH --execute-proof --json" in requested_handover
        and "valid live-client workflow proof artifact" in requested_handover
    )
    requested_handover_scope_output_route_valid = (
        requested_handover_path.exists()
        and "--approval-output PATH --scope-packet-output PATH --json" in requested_handover
        and (
            "routes `next_command` to `real-client-input-manifest` with both `--approval-output PATH` "
            "and `--scope-packet-output PATH`"
        )
        in requested_handover
    )
    requested_handover_alias_valid = (
        requested_handover_alias_valid
        and requested_handover_next_pass_valid
        and requested_handover_scope_output_route_valid
    )
    passover_valid = (
        passover_path.exists()
        and _contains_external_readiness_status(passover)
        and "Do not mark VentureOps COMPLETE" in passover
        and "live client workflow" in passover
        and "live revenue workflow" in passover
        and "Completion Rule" in passover
    )
    proof_chain_valid = (
        len(existing_artifacts) == len(expected_artifacts)
        and bool(contract)
        and bool(scorecard)
        and contract.get("status") == "blocked_real_client_scope_required"
        and metrics.get("live_client_scope_contract_written") is True
    )
    live_client_proof_present = bool(external_completion_artifacts["live_client_workflow_proof_present"])
    live_revenue_proof_present = bool(external_completion_artifacts["live_revenue_workflow_proof_present"])
    final_bundle_validation_ready = bool(final_bundle_validation_reports["final_evidence_bundle_validation_ready"])
    current_status = (
        EXTERNAL_READINESS_LIVE_CLIENT_VERIFIED_STATUS
        if live_client_proof_present
        else EXTERNAL_READINESS_INITIAL_STATUS
    )

    tdd_evidence = [
        "runtime/ventureops/test_ventureops.py",
        "runtime/ventureops/test_agent_runtime_governance_audit_workflow.py",
        "07_LOGS/Build-Logs/2026-05-11-ChaseOS-ventureops-live-client-scope-contract.md",
        "07_LOGS/Build-Logs/2026-05-11-ChaseOS-ventureops-scope-evidence-approval-prerequisite.md",
        "07_LOGS/Build-Logs/2026-05-11-ChaseOS-ventureops-scope-evidence-full-validation-cli.md",
        "07_LOGS/Build-Logs/2026-05-11-ChaseOS-ventureops-externaal-handover-next-pass-correction.md",
        "07_LOGS/Build-Logs/2026-05-11-ChaseOS-ventureops-audit-next-real-use-pass.md",
        "07_LOGS/Build-Logs/2026-05-11-ChaseOS-ventureops-closeout-next-real-use-pass.md",
        "07_LOGS/Build-Logs/2026-05-11-ChaseOS-ventureops-runbook-next-real-use-pass.md",
        "07_LOGS/Build-Logs/2026-05-11-ChaseOS-ventureops-runbook-invalid-packet-status-hardening.md",
        "07_LOGS/Build-Logs/2026-05-11-ChaseOS-ventureops-runbook-live-client-readiness-fields.md",
        "07_LOGS/Build-Logs/2026-05-11-ChaseOS-ventureops-runbook-contract-readiness-disclosure.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-proof-cli-dynamic-date-default.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-real-client-input-manifest.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-evidence-intake-workflow-proof-routing.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-live-client-readiness-workflow-proof-routing.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-completion-audit-current-truth-sync.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-final-runbook-real-client-input-routing.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-real-client-input-manifest-dated-report-default.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-live-revenue-readiness-report-freshness.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-evidence-discovery-real-client-input-routing.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-real-client-manifest-output-requirement.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-real-client-manifest-scope-output-requirement.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-final-runbook-scope-output-routing.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-externaal-scope-output-validation.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-feature-audit-externaal-route-surface.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-no-evidence-manifest-scope-output-routing.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-evidence-packet-output-collision-guard.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-guarded-proof-output-collision-guard.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-revenue-completion-reference-revalidation.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-live-client-source-digest-validation.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-live-client-completion-reference-revalidation.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-live-client-reference-consistency-validation.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-revenue-reference-consistency-validation.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-receipt-artifact-validation.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-final-evidence-bundle-validation.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-final-runbook-bundle-validation-step.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-final-evidence-bundle-packet-builder.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-final-runbook-bundle-packet-authoring-step.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-final-bundle-packet-path-guard.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-external-packet-path-guard.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-final-bundle-validation-completion-gate.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-feature-audit-success-criteria-final-bundle.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-real-client-manifest-output-path-guard.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-final-bundle-validation-report-write-guard.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-final-bundle-validation-report-dated-default.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-final-bundle-validation-report-default-collision-guard.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-real-client-manifest-report-write-guard.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-live-client-scope-packet-reference-revalidation.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-live-revenue-packet-reference-revalidation.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-final-bundle-report-reference-revalidation.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-final-runbook-validation-report-write-route.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-final-audit-report-write-route.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-final-audit-report-write-guard.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-external-readiness-audit-report-write-guard.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-final-runbook-report-write-guard.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-real-evidence-closeout-report-write-guard.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-evidence-intake-report-write-guard.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-real-client-manifest-report-audit-flags.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-real-client-manifest-contract-report-disclosure.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-live-readiness-report-write-guard.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-client-safe-delivery-artifact-validation.md",
    ]
    tdd_verified = all((root / path).exists() for path in tdd_evidence)
    scope_contract_evidence = [
        scope_schema_rel,
        scope_template_rel,
        "runtime.ventureops.validation.validate_real_client_scope_evidence",
        "runtime.ventureops.validation.validate_scope_evidence_approval_artifact",
    ]
    scope_contract_verified = (root / scope_schema_rel).exists() and (root / scope_template_rel).exists()
    scope_approval_contract_evidence = [
        scope_approval_schema_rel,
        scope_approval_template_rel,
        "runtime.ventureops.validation.validate_real_client_scope_approval_artifact",
    ]
    scope_approval_contract_verified = (
        (root / scope_approval_schema_rel).exists() and (root / scope_approval_template_rel).exists()
    )
    revenue_contract_evidence = [
        revenue_schema_rel,
        revenue_template_rel,
        "runtime.ventureops.validation.validate_live_revenue_evidence",
    ]
    revenue_contract_verified = (root / revenue_schema_rel).exists() and (root / revenue_template_rel).exists()
    readiness_contract_evidence = [
        readiness_module_rel,
        readiness_cli_rel,
        "chaseos ventureops live-client-proof-readiness",
    ]
    readiness_contract_verified = (root / readiness_module_rel).exists() and (root / readiness_cli_rel).exists()
    revenue_readiness_contract_evidence = [
        revenue_readiness_module_rel,
        readiness_cli_rel,
        "chaseos ventureops live-revenue-proof-readiness",
    ]
    revenue_readiness_contract_verified = (
        (root / revenue_readiness_module_rel).exists() and (root / readiness_cli_rel).exists()
    )
    evidence_intake_cli_evidence = [
        evidence_intake_module_rel,
        readiness_cli_rel,
        "chaseos ventureops evidence-intake",
    ]
    evidence_intake_cli_valid = (
        (root / evidence_intake_module_rel).exists()
        and (root / readiness_cli_rel).exists()
        and '"evidence-intake"' in command_contract
        and "cmd_ventureops_evidence_intake" in command_contract
    )
    evidence_intake_report_write_guard_evidence = [
        readiness_cli_rel,
        "runtime/ventureops/test_ventureops.py",
    ]
    evidence_intake_report_write_guard_valid = (
        "report path already exists" in cli_text
        and "report_path escapes vault root" in cli_text
        and "report_write_blocked" in cli_text
        and "fail-closed-if-evidence-intake-report-exists-or-escapes-vault-root" in command_contract
        and "test_ventureops_evidence_intake_cli_blocks_existing_report_path_without_overwrite" in test_text
        and "test_ventureops_evidence_intake_cli_blocks_escaped_report_path_without_traceback" in test_text
    )
    evidence_intake_report_dated_default_evidence = [
        readiness_cli_rel,
        "runtime/ventureops/test_ventureops.py",
    ]
    evidence_intake_report_dated_default_valid = (
        "_ventureops-evidence-intake-report.json" in cli_text
        and "_default_proof_date()" in cli_text
        and "default-write:dated-evidence-intake-report-with---write-report" in command_contract
        and "test_ventureops_evidence_intake_cli_write_report_defaults_to_dated_report_path" in test_text
    )
    evidence_intake_report_default_collision_guard_evidence = [
        readiness_cli_rel,
        "runtime/ventureops/test_ventureops.py",
    ]
    evidence_intake_report_default_collision_guard_valid = (
        "_next_available_default_report_path" in cli_text
        and "while (vault_root / candidate).exists()" in cli_text
        and "default-write:collision-safe-suffixed-evidence-intake-report" in command_contract
        and "test_ventureops_evidence_intake_cli_write_report_uses_collision_safe_default_path" in test_text
    )
    evidence_discovery_preflight_cli_evidence = [
        evidence_discovery_preflight_module_rel,
        readiness_cli_rel,
        "chaseos ventureops evidence-discovery-preflight",
    ]
    evidence_discovery_preflight_cli_valid = (
        (root / evidence_discovery_preflight_module_rel).exists()
        and (root / readiness_cli_rel).exists()
        and '"evidence-discovery-preflight"' in command_contract
        and "cmd_ventureops_evidence_discovery_preflight" in command_contract
    )
    real_client_input_manifest_cli_evidence = [
        real_client_input_manifest_module_rel,
        readiness_cli_rel,
        "chaseos ventureops real-client-input-manifest",
    ]
    real_client_input_manifest_cli_valid = (
        (root / real_client_input_manifest_module_rel).exists()
        and (root / readiness_cli_rel).exists()
        and '"real-client-input-manifest"' in command_contract
        and "cmd_ventureops_real_client_input_manifest" in command_contract
    )
    real_client_input_manifest_text = _read_text_if_exists(root / real_client_input_manifest_module_rel)
    real_client_input_manifest_report_write_guard_evidence = [
        real_client_input_manifest_module_rel,
        readiness_cli_rel,
        "runtime/ventureops/test_ventureops.py",
    ]
    real_client_input_manifest_report_write_guard_valid = (
        "report path already exists" in real_client_input_manifest_text
        and "report_path escapes vault root" in real_client_input_manifest_text
        and "report_write_blocked" in real_client_input_manifest_text
        and "_next_available_default_report_path" in cli_text
        and "default-write:dated-real-client-input-manifest-report-with---write-report" in command_contract
        and "default-write:collision-safe-suffixed-real-client-input-manifest-report" in command_contract
        and "fail-closed-if-real-client-input-manifest-report-exists-or-escapes-vault-root" in command_contract
        and "test_real_client_input_manifest_cli_write_report_uses_collision_safe_default_path" in test_text
        and "test_real_client_input_manifest_cli_blocks_existing_report_path_without_overwrite" in test_text
        and "test_real_client_input_manifest_cli_blocks_escaped_report_path_without_traceback" in test_text
    )
    real_client_input_manifest_report_dated_default_evidence = [
        readiness_cli_rel,
        "runtime/ventureops/test_ventureops.py",
    ]
    real_client_input_manifest_report_dated_default_valid = (
        "_ventureops-real-client-input-manifest.json" in cli_text
        and "_default_proof_date()" in cli_text
        and "default-write:dated-real-client-input-manifest-report-with---write-report" in command_contract
        and "test_real_client_input_manifest_cli_write_report_defaults_to_dated_path" in test_text
        and "test_ventureops_real_client_input_manifest_contract_discloses_distinct_report_defaults" in test_text
    )
    real_client_input_manifest_report_default_collision_guard_evidence = [
        readiness_cli_rel,
        "runtime/ventureops/test_ventureops.py",
    ]
    real_client_input_manifest_report_default_collision_guard_valid = (
        "_next_available_default_report_path" in cli_text
        and "default-write:collision-safe-suffixed-real-client-input-manifest-report" in command_contract
        and "test_real_client_input_manifest_cli_write_report_uses_collision_safe_default_path" in test_text
        and "test_ventureops_real_client_input_manifest_contract_discloses_distinct_report_defaults" in test_text
    )
    scope_approval_packet_builder_cli_evidence = [
        scope_approval_packet_builder_module_rel,
        readiness_cli_rel,
        "chaseos ventureops scope-approval-packet",
    ]
    scope_approval_packet_builder_cli_valid = (
        (root / scope_approval_packet_builder_module_rel).exists()
        and (root / readiness_cli_rel).exists()
        and '"scope-approval-packet"' in command_contract
        and "cmd_ventureops_scope_approval_packet" in command_contract
    )
    scope_evidence_packet_builder_cli_evidence = [
        scope_evidence_packet_builder_module_rel,
        readiness_cli_rel,
        "chaseos ventureops scope-evidence-packet",
    ]
    scope_evidence_packet_builder_cli_valid = (
        (root / scope_evidence_packet_builder_module_rel).exists()
        and (root / readiness_cli_rel).exists()
        and '"scope-evidence-packet"' in command_contract
        and "cmd_ventureops_scope_evidence_packet" in command_contract
    )
    revenue_evidence_packet_builder_cli_evidence = [
        revenue_evidence_packet_builder_module_rel,
        readiness_cli_rel,
        "chaseos ventureops revenue-evidence-packet",
    ]
    revenue_evidence_packet_builder_cli_valid = (
        (root / revenue_evidence_packet_builder_module_rel).exists()
        and (root / readiness_cli_rel).exists()
        and '"revenue-evidence-packet"' in command_contract
        and "cmd_ventureops_revenue_evidence_packet" in command_contract
    )
    delivery_proof_packet_builder_cli_evidence = [
        delivery_proof_packet_builder_module_rel,
        readiness_cli_rel,
        "chaseos ventureops delivery-proof-packet",
    ]
    delivery_proof_packet_builder_cli_valid = (
        (root / delivery_proof_packet_builder_module_rel).exists()
        and (root / readiness_cli_rel).exists()
        and '"delivery-proof-packet"' in command_contract
        and "cmd_ventureops_delivery_proof_packet" in command_contract
    )
    external_packet_output_collision_guard_evidence = [
        scope_approval_packet_builder_module_rel,
        scope_evidence_packet_builder_module_rel,
        delivery_proof_packet_builder_module_rel,
        revenue_evidence_packet_builder_module_rel,
        "runtime/ventureops/test_ventureops.py",
    ]
    packet_builder_texts = [
        _read_text_if_exists(root / scope_approval_packet_builder_module_rel),
        _read_text_if_exists(root / scope_evidence_packet_builder_module_rel),
        _read_text_if_exists(root / delivery_proof_packet_builder_module_rel),
        _read_text_if_exists(root / revenue_evidence_packet_builder_module_rel),
    ]
    external_packet_output_collision_guard_valid = (
        all((root / path).exists() for path in external_packet_output_collision_guard_evidence[:4])
        and all("output path already exists:" in text and "output_path_available" in text for text in packet_builder_texts)
        and "test_ventureops_external_packet_builders_reject_existing_output_paths"
        in _read_text_if_exists(root / "runtime/ventureops/test_ventureops.py")
    )
    external_packet_path_guard_evidence = [
        scope_approval_packet_builder_module_rel,
        scope_evidence_packet_builder_module_rel,
        delivery_proof_packet_builder_module_rel,
        revenue_evidence_packet_builder_module_rel,
        "runtime/ventureops/test_ventureops.py",
    ]
    external_packet_path_guard_valid = (
        all((root / path).exists() for path in external_packet_path_guard_evidence[:4])
        and "approved_read_paths" in packet_builder_texts[0]
        and "approval_artifact_path" in packet_builder_texts[1]
        and "client_safe_delivery_artifact_path" in packet_builder_texts[2]
        and "receipt_artifact_path" in packet_builder_texts[3]
        and all("_add_relative_path" in text and "escapes vault root" in text for text in packet_builder_texts)
        and "test_ventureops_external_packet_builders_block_escaped_paths_without_exception" in test_text
    )
    real_evidence_closeout_cli_evidence = [
        real_evidence_closeout_module_rel,
        readiness_cli_rel,
        "chaseos ventureops real-evidence-closeout-readiness",
    ]
    real_evidence_closeout_readiness_cli_valid = (
        (root / real_evidence_closeout_module_rel).exists()
        and (root / readiness_cli_rel).exists()
        and '"real-evidence-closeout-readiness"' in command_contract
        and "cmd_ventureops_real_evidence_closeout_readiness" in command_contract
    )
    real_evidence_closeout_report_write_guard_evidence = [
        readiness_cli_rel,
        "runtime/ventureops/test_ventureops.py",
    ]
    real_evidence_closeout_report_write_guard_valid = (
        "report path already exists" in cli_text
        and "report_path escapes vault root" in cli_text
        and "report_write_blocked" in cli_text
        and "fail-closed-if-real-evidence-closeout-readiness-report-exists-or-escapes-vault-root"
        in command_contract
        and "test_real_evidence_closeout_readiness_cli_blocks_existing_report_path_without_overwrite" in test_text
        and "test_real_evidence_closeout_readiness_cli_blocks_escaped_report_path_without_traceback" in test_text
    )
    real_evidence_closeout_report_dated_default_evidence = [
        readiness_cli_rel,
        "runtime/ventureops/test_ventureops.py",
    ]
    real_evidence_closeout_report_dated_default_valid = (
        "_ventureops-real-evidence-closeout-readiness-report.json" in cli_text
        and "_default_proof_date()" in cli_text
        and "default-write:dated-real-evidence-closeout-readiness-report-with---write-report" in command_contract
        and "test_real_evidence_closeout_readiness_cli_write_report_defaults_to_dated_report_path" in test_text
    )
    real_evidence_closeout_report_default_collision_guard_evidence = [
        readiness_cli_rel,
        "runtime/ventureops/test_ventureops.py",
    ]
    real_evidence_closeout_report_default_collision_guard_valid = (
        "_next_available_default_report_path" in cli_text
        and "while (vault_root / candidate).exists()" in cli_text
        and "default-write:collision-safe-suffixed-real-evidence-closeout-readiness-report" in command_contract
        and "test_real_evidence_closeout_readiness_cli_write_report_uses_collision_safe_default_path" in test_text
    )
    feature_family_completion_audit_cli_evidence = [
        feature_family_completion_audit_module_rel,
        readiness_cli_rel,
        "chaseos ventureops feature-family-completion-audit",
    ]
    feature_family_completion_audit_cli_valid = (
        (root / feature_family_completion_audit_module_rel).exists()
        and (root / readiness_cli_rel).exists()
        and '"feature-family-completion-audit"' in command_contract
        and "cmd_ventureops_feature_family_completion_audit" in command_contract
    )
    feature_family_completion_audit_text = _read_text_if_exists(root / feature_family_completion_audit_module_rel)
    feature_family_completion_audit_report_write_guard_evidence = [
        feature_family_completion_audit_module_rel,
        readiness_cli_rel,
        "runtime/ventureops/test_ventureops.py",
    ]
    feature_family_completion_audit_report_write_guard_valid = (
        "report path already exists" in feature_family_completion_audit_text
        and "report_path escapes vault root" in feature_family_completion_audit_text
        and "report_write_blocked" in feature_family_completion_audit_text
        and "fail-closed-if-feature-family-completion-audit-report-exists-or-escapes-vault-root"
        in command_contract
        and "test_feature_family_completion_audit_cli_blocks_existing_report_path_without_overwrite" in test_text
        and "test_feature_family_completion_audit_cli_blocks_escaped_report_path_without_traceback" in test_text
    )
    feature_family_completion_audit_report_dated_default_evidence = [
        readiness_cli_rel,
        "runtime/ventureops/test_ventureops.py",
    ]
    feature_family_completion_audit_report_dated_default_valid = (
        "_ventureops-feature-family-completion-audit-report.json" in cli_text
        and "_default_proof_date()" in cli_text
        and "default-write:dated-feature-family-completion-audit-report-with---write-report" in command_contract
        and "test_feature_family_completion_audit_cli_write_report_defaults_to_dated_report_path" in test_text
    )
    feature_family_completion_audit_report_default_collision_guard_evidence = [
        readiness_cli_rel,
        "runtime/ventureops/test_ventureops.py",
    ]
    feature_family_completion_audit_report_default_collision_guard_valid = (
        "_next_available_default_report_path" in cli_text
        and "while (vault_root / candidate).exists()" in cli_text
        and "default-write:collision-safe-suffixed-feature-family-completion-audit-report" in command_contract
        and "test_feature_family_completion_audit_cli_write_report_uses_collision_safe_default_path" in test_text
    )
    final_external_execution_runbook_cli_evidence = [
        final_external_execution_runbook_module_rel,
        readiness_cli_rel,
        "chaseos ventureops final-external-execution-runbook",
    ]
    final_external_execution_runbook_cli_valid = (
        (root / final_external_execution_runbook_module_rel).exists()
        and (root / readiness_cli_rel).exists()
        and '"final-external-execution-runbook"' in command_contract
        and "cmd_ventureops_final_external_execution_runbook" in command_contract
        and "final evidence bundle validation" in final_external_execution_runbook_text
        and "chaseos ventureops final-evidence-bundle --bundle PATH " in final_external_execution_runbook_text
        and "--write-report --report-path PATH --json" in final_external_execution_runbook_text
        and "final evidence bundle packet authoring" in final_external_execution_runbook_text
        and "chaseos ventureops final-evidence-bundle-packet" in final_external_execution_runbook_text
    )
    final_external_runbook_report_write_guard_evidence = [
        readiness_cli_rel,
        "runtime/ventureops/test_ventureops.py",
    ]
    final_external_runbook_report_write_guard_valid = (
        "report path already exists" in cli_text
        and "report_path escapes vault root" in cli_text
        and "report_write_blocked" in cli_text
        and "fail-closed-if-final-external-runbook-report-exists-or-escapes-vault-root" in command_contract
        and "test_final_external_execution_runbook_cli_blocks_existing_report_path_without_overwrite" in test_text
        and "test_final_external_execution_runbook_cli_blocks_escaped_report_path_without_traceback" in test_text
    )
    final_external_runbook_report_dated_default_evidence = [
        readiness_cli_rel,
        "runtime/ventureops/test_ventureops.py",
    ]
    final_external_runbook_report_dated_default_valid = (
        "_ventureops-final-external-execution-runbook-report.json" in cli_text
        and "_default_proof_date()" in cli_text
        and "default-write:dated-final-external-runbook-report-with---write-report" in command_contract
        and "test_final_external_execution_runbook_cli_write_report_defaults_to_dated_report_path" in test_text
    )
    final_external_runbook_report_default_collision_guard_evidence = [
        readiness_cli_rel,
        "runtime/ventureops/test_ventureops.py",
    ]
    final_external_runbook_report_default_collision_guard_valid = (
        "_next_available_default_report_path" in cli_text
        and "while (vault_root / candidate).exists()" in cli_text
        and "default-write:collision-safe-suffixed-final-external-runbook-report" in command_contract
        and "test_final_external_execution_runbook_cli_write_report_uses_collision_safe_default_path" in test_text
    )
    final_evidence_bundle_validator_evidence = [
        final_external_evidence_bundle_module_rel,
        readiness_cli_rel,
        "chaseos ventureops final-evidence-bundle",
    ]
    final_evidence_bundle_validator_valid = (
        (root / final_external_evidence_bundle_module_rel).exists()
        and (root / readiness_cli_rel).exists()
        and '"final-evidence-bundle"' in command_contract
        and "cmd_ventureops_final_evidence_bundle" in command_contract
        and "validate_final_external_evidence_bundle" in _read_text_if_exists(
            root / final_external_evidence_bundle_module_rel
        )
        and "test_final_external_evidence_bundle_validation_accepts_complete_proof_chain" in test_text
    )
    final_evidence_bundle_validation_report_write_guard_evidence = [
        final_external_evidence_bundle_module_rel,
        "runtime/ventureops/test_ventureops.py",
    ]
    final_external_evidence_bundle_text = _read_text_if_exists(root / final_external_evidence_bundle_module_rel)
    final_evidence_bundle_validation_report_write_guard_valid = (
        "report path already exists" in final_external_evidence_bundle_text
        and "report_path escapes vault root" in final_external_evidence_bundle_text
        and "report_write_blocked" in final_external_evidence_bundle_text
        and "fail-closed-if-report-exists-or-escapes-vault-root" in command_contract
        and "test_final_evidence_bundle_cli_blocks_existing_report_path_without_overwrite" in test_text
        and "test_final_evidence_bundle_cli_blocks_escaped_report_path_without_traceback" in test_text
    )
    final_evidence_bundle_validation_report_dated_default_evidence = [
        readiness_cli_rel,
        "runtime/ventureops/test_ventureops.py",
    ]
    final_evidence_bundle_validation_report_dated_default_valid = (
        "_ventureops-final-evidence-bundle-validation-report.json" in cli_text
        and "_default_proof_date()" in cli_text
        and "default-write:dated-final-evidence-bundle-validation-report-with---write-report" in command_contract
        and "test_final_evidence_bundle_cli_write_report_defaults_to_dated_report_path" in test_text
    )
    final_evidence_bundle_validation_report_default_collision_guard_evidence = [
        readiness_cli_rel,
        "runtime/ventureops/test_ventureops.py",
    ]
    final_evidence_bundle_validation_report_default_collision_guard_valid = (
        "_next_available_default_report_path" in cli_text
        and "while (vault_root / candidate).exists()" in cli_text
        and "default-write:collision-safe-suffixed-final-evidence-bundle-validation-report" in command_contract
        and "test_final_evidence_bundle_cli_write_report_uses_collision_safe_default_path" in test_text
    )
    final_evidence_bundle_packet_builder_evidence = [
        final_evidence_bundle_packet_builder_module_rel,
        readiness_cli_rel,
        "chaseos ventureops final-evidence-bundle-packet",
    ]
    final_evidence_bundle_packet_builder_cli_valid = (
        (root / final_evidence_bundle_packet_builder_module_rel).exists()
        and (root / readiness_cli_rel).exists()
        and '"final-evidence-bundle-packet"' in command_contract
        and "cmd_ventureops_final_evidence_bundle_packet" in command_contract
        and "build_final_evidence_bundle_packet" in _read_text_if_exists(
            root / final_evidence_bundle_packet_builder_module_rel
        )
        and "test_final_evidence_bundle_packet_builder_writes_guarded_bundle" in test_text
    )
    final_evidence_bundle_packet_path_guard_evidence = [
        final_evidence_bundle_packet_builder_module_rel,
        "runtime/ventureops/test_ventureops.py",
    ]
    final_evidence_bundle_packet_path_guard_valid = (
        "output_path escapes vault root" in _read_text_if_exists(root / final_evidence_bundle_packet_builder_module_rel)
        and "_add_relative_path" in _read_text_if_exists(root / final_evidence_bundle_packet_builder_module_rel)
        and "test_final_evidence_bundle_packet_builder_blocks_escaped_paths_without_exception" in test_text
        and "test_final_evidence_bundle_packet_cli_blocks_escaped_output_without_traceback" in test_text
    )
    final_evidence_bundle_report_reference_revalidation_evidence = [
        "runtime.ventureops.validation.discover_final_evidence_bundle_validation_reports",
        "runtime.ventureops.final_external_evidence_bundle.validate_final_external_evidence_bundle",
        "runtime/ventureops/test_ventureops.py",
    ]
    final_evidence_bundle_report_reference_revalidation_valid = (
        "report bundle_path is not currently valid" in validation_text
        and "validate_final_external_evidence_bundle(root, bundle_path=bundle_path)" in validation_text
        and "test_external_readiness_completion_audit_revalidates_final_bundle_report_bundle_path" in test_text
    )
    scope_source_path_verifier_evidence = [
        "runtime.ventureops.validation.validate_scope_evidence_source_paths",
        readiness_module_rel,
        evidence_intake_module_rel,
        live_client_scope_proof_module_rel,
    ]
    scope_source_probe = validate_scope_evidence_source_paths(root, ["README.md"])
    scope_source_path_verifier_valid = (
        scope_source_probe["ok"] is True
        and (root / readiness_module_rel).exists()
        and (root / evidence_intake_module_rel).exists()
        and (root / live_client_scope_proof_module_rel).exists()
    )
    live_client_proof_artifact_verifier_evidence = [
        "runtime.ventureops.validation.validate_live_client_scope_proof_artifact",
        "runtime.ventureops.validation.validate_live_client_workflow_proof_artifact",
        live_client_workflow_proof_module_rel,
        live_revenue_proof_module_rel,
        evidence_intake_module_rel,
    ]
    verifier_probe = validate_live_client_scope_proof_artifact(
        {
            "type": "ventureops-live-client-scope-proof-gate",
            "workflow_id": "agent_runtime_governance_audit",
            "run_id": "probe-live-client-proof",
            "date": "2026-05-11",
            "status": "real_client_scope_evidence_validated_no_live_client_run",
            "proof_path": "07_LOGS/Workflow-Proofs/probe.md",
            "live_client_scope_contract_path": "07_LOGS/Workflow-Proofs/probe-contract.json",
            "real_client_scope_evidence_path": "runtime/ventureops/fixtures/scope-evidence/probe.json",
            "client_approved_scope_id": "scope-probe",
            "client_label": "Probe Client",
            "approval_id": "approval-probe",
            "approval_status": "approved",
            "redaction_policy": "client_safe_summary_only",
            "delivery_boundary": "no_external_delivery",
            "approved_read_path_count": 1,
            "approved_read_paths_validated": True,
            "approved_read_paths": ["03_INPUTS/probe/redacted-brief.md"],
            "real_client_scope_present": True,
            "real_client_scope_approved": True,
            "live_client_scope_proof_performed": False,
            "live_client_data_ingested": False,
            "live_external_delivery_performed": False,
            "forbidden_actions": ["external_send"],
            "next_required_pass": "ventureops-live-client-scope-proof",
        }
    )
    live_client_proof_artifact_verifier_valid = (
        verifier_probe["ok"] is True
        and (root / live_client_workflow_proof_module_rel).exists()
        and (root / live_revenue_proof_module_rel).exists()
        and (root / evidence_intake_module_rel).exists()
    )
    live_delivery_proof_artifact_verifier_evidence = [
        "runtime.ventureops.validation.validate_live_delivery_proof_artifact",
        live_revenue_proof_module_rel,
        revenue_readiness_module_rel,
        evidence_intake_module_rel,
        evidence_discovery_preflight_module_rel,
        revenue_evidence_packet_builder_module_rel,
        delivery_proof_packet_builder_module_rel,
    ]
    live_delivery_proof_probe = validate_live_delivery_proof_artifact(
        {
            "type": "ventureops-live-delivery-proof",
            "status": "operator_attested_delivery_recorded",
            "delivery_proof_id": "delivery-probe",
            "workflow_id": "agent_runtime_governance_audit",
            "client_label": "Probe Client",
            "delivery_reference_id": "delivery-ref-probe",
            "delivery_status": "delivered",
            "client_safe_delivery_artifact_path": "07_LOGS/Workflow-Proofs/probe-delivery.md",
            "live_client_proof_path": "07_LOGS/Workflow-Proofs/probe-live-client-workflow-proof.json",
            "delivery_boundary": "operator_attested_delivery_no_chaseos_external_send",
            "operator_attested_delivery_performed": True,
            "external_send_performed_by_chaseos": False,
            "crm_mutation_performed": False,
            "payment_mutation_performed": False,
            "invoice_sent": False,
            "provider_calls": 0,
            "browser_actions": 0,
            "revenue_claim_made": False,
        }
    )
    live_delivery_proof_artifact_verifier_valid = (
        live_delivery_proof_probe["ok"] is True
        and (root / live_revenue_proof_module_rel).exists()
        and (root / revenue_readiness_module_rel).exists()
        and (root / evidence_intake_module_rel).exists()
        and (root / evidence_discovery_preflight_module_rel).exists()
        and (root / revenue_evidence_packet_builder_module_rel).exists()
        and (root / delivery_proof_packet_builder_module_rel).exists()
    )
    live_client_scope_proof_cli_evidence = [
        live_client_scope_proof_module_rel,
        readiness_cli_rel,
        "chaseos ventureops live-client-scope-proof",
    ]
    live_client_scope_proof_cli_valid = (
        (root / live_client_scope_proof_module_rel).exists()
        and (root / readiness_cli_rel).exists()
        and '"live-client-scope-proof"' in command_contract
        and "cmd_ventureops_live_client_scope_proof" in command_contract
    )
    live_client_workflow_proof_cli_evidence = [
        live_client_workflow_proof_module_rel,
        readiness_cli_rel,
        "chaseos ventureops live-client-workflow-proof",
    ]
    live_client_workflow_proof_probe = validate_live_client_workflow_proof_artifact(
        {
            "type": "ventureops-live-client-workflow-proof",
            "status": "live_client_workflow_proof_written",
            "workflow_id": "agent_runtime_governance_audit",
            "run_id": "probe-live-client-workflow-proof",
            "date": "2026-05-11",
            "scope_packet_path": "03_INPUTS/probe/scope-evidence.json",
            "client_approved_scope_id": "scope-probe",
            "client_label": "Probe Client",
            "approval_id": "approval-probe",
            "approval_status": "approved",
            "approved_read_paths": ["03_INPUTS/probe/redacted-brief.md"],
            "approved_read_path_count": 1,
            "source_digest_count": 1,
            "source_digests": [
                {
                    "path": "03_INPUTS/probe/redacted-brief.md",
                    "sha256": "a" * 64,
                    "byte_count": 128,
                }
            ],
            "scope_proof_gate_path": "07_LOGS/Workflow-Proofs/probe-live-client-scope-proof-gate.json",
            "client_report_path": "07_LOGS/Workflow-Proofs/probe-client-report.md",
            "scorecard_path": "07_LOGS/Workflow-Proofs/probe-scorecard.json",
            "live_client_workflow_proof_performed": True,
            "scoped_client_data_ingested": True,
            "broad_client_data_ingested": False,
            "live_external_delivery_performed": False,
            "external_send_performed": False,
            "crm_mutation_performed": False,
            "payment_mutation_performed": False,
            "provider_calls": 0,
            "browser_actions": 0,
            "revenue_claim_made": False,
        }
    )
    live_client_workflow_proof_cli_valid = (
        live_client_workflow_proof_probe["ok"] is True
        and (root / live_client_workflow_proof_module_rel).exists()
        and (root / readiness_cli_rel).exists()
        and '"live-client-workflow-proof"' in command_contract
        and "cmd_ventureops_live_client_workflow_proof" in command_contract
    )
    live_revenue_proof_cli_evidence = [
        live_revenue_proof_module_rel,
        readiness_cli_rel,
        "chaseos ventureops live-revenue-proof",
    ]
    live_revenue_proof_cli_valid = (
        (root / live_revenue_proof_module_rel).exists()
        and (root / readiness_cli_rel).exists()
        and '"live-revenue-proof"' in command_contract
        and "cmd_ventureops_live_revenue_proof" in command_contract
    )
    guarded_proof_output_collision_guard_evidence = [
        live_client_scope_proof_module_rel,
        live_client_workflow_proof_module_rel,
        live_revenue_proof_module_rel,
        "runtime/ventureops/test_ventureops.py",
    ]
    proof_writer_texts = [
        _read_text_if_exists(root / live_client_scope_proof_module_rel),
        _read_text_if_exists(root / live_client_workflow_proof_module_rel),
        _read_text_if_exists(root / live_revenue_proof_module_rel),
    ]
    guarded_proof_output_collision_guard_valid = (
        all((root / path).exists() for path in guarded_proof_output_collision_guard_evidence[:3])
        and all("proof output path already exists" in text for text in proof_writer_texts)
        and "test_ventureops_guarded_proof_commands_reject_existing_proof_outputs"
        in _read_text_if_exists(root / "runtime/ventureops/test_ventureops.py")
    )
    revenue_completion_reference_revalidation_evidence = [
        "runtime.ventureops.validation.discover_external_completion_artifacts",
        "runtime.ventureops.validation.validate_live_delivery_proof_artifact",
        "runtime/ventureops/test_ventureops.py",
    ]
    validation_text = _read_text_if_exists(root / "runtime/ventureops/validation.py")
    test_text = _read_text_if_exists(root / "runtime/ventureops/test_ventureops.py")
    revenue_completion_reference_revalidation_valid = (
        "receipt artifact missing" in validation_text
        and "delivery proof artifact missing" in validation_text
        and "client-safe delivery artifact missing" in validation_text
        and "test_external_completion_artifact_discovery_revalidates_revenue_referenced_files" in test_text
    )
    live_revenue_packet_reference_revalidation_evidence = [
        "runtime.ventureops.validation.discover_external_completion_artifacts",
        "runtime.ventureops.validation.validate_live_revenue_evidence",
        "runtime/ventureops/test_ventureops.py",
    ]
    live_revenue_packet_reference_revalidation_valid = (
        "revenue packet artifact missing" in validation_text
        and "revenue packet artifact invalid" in validation_text
        and "revenue packet amount does not match revenue proof" in validation_text
        and "test_external_completion_artifact_discovery_revalidates_live_revenue_packet" in test_text
    )
    live_client_source_digest_validation_evidence = [
        "runtime.ventureops.validation.validate_live_client_workflow_proof_artifact",
        live_client_workflow_proof_module_rel,
        "runtime/ventureops/test_ventureops.py",
    ]
    live_client_source_digest_validation_valid = (
        '"source_digests"' in validation_text
        and "source_digests must cover approved_read_paths" in validation_text
        and "source_digest_count must match source_digests" in validation_text
        and "test_validate_live_client_workflow_proof_artifact_rejects_missing_or_invalid_source_digests"
        in test_text
    )
    live_client_completion_reference_revalidation_evidence = [
        "runtime.ventureops.validation.discover_external_completion_artifacts",
        "runtime.ventureops.validation.validate_live_client_scope_proof_artifact",
        "runtime.ventureops.validation.validate_agent_scorecard",
        "runtime/ventureops/test_ventureops.py",
    ]
    live_client_completion_reference_revalidation_valid = (
        "scope proof gate artifact missing" in validation_text
        and "client report artifact missing" in validation_text
        and "scorecard artifact missing" in validation_text
        and "test_external_completion_artifact_discovery_revalidates_live_client_referenced_files"
        in test_text
    )
    live_client_scope_packet_reference_revalidation_evidence = [
        "runtime.ventureops.validation.discover_external_completion_artifacts",
        "runtime.ventureops.validation.validate_real_client_scope_evidence",
        "runtime.ventureops.validation.validate_scope_evidence_approval_artifact",
        "runtime.ventureops.validation.validate_scope_evidence_source_paths",
        "runtime/ventureops/test_ventureops.py",
    ]
    live_client_scope_packet_reference_revalidation_valid = (
        "scope packet artifact missing" in validation_text
        and "scope packet approval artifact invalid" in validation_text
        and "scope packet source path invalid" in validation_text
        and "test_external_completion_artifact_discovery_revalidates_live_client_scope_packet"
        in test_text
    )
    live_client_reference_consistency_validation_evidence = [
        "runtime.ventureops.validation.discover_external_completion_artifacts",
        "runtime.ventureops.validation.validate_live_client_scope_proof_artifact",
        "runtime.ventureops.validation.validate_agent_scorecard",
        "runtime/ventureops/test_ventureops.py",
    ]
    live_client_reference_consistency_validation_valid = (
        "scope proof gate client_approved_scope_id does not match live-client workflow proof" in validation_text
        and "scope proof gate approved_read_paths do not match live-client workflow proof" in validation_text
        and "scorecard run_id does not match live-client workflow proof" in validation_text
        and "test_external_completion_artifact_discovery_rejects_inconsistent_live_client_references"
        in test_text
    )
    revenue_reference_consistency_validation_evidence = [
        "runtime.ventureops.validation.discover_external_completion_artifacts",
        "runtime.ventureops.validation.validate_live_delivery_proof_artifact",
        "runtime/ventureops/test_ventureops.py",
    ]
    revenue_reference_consistency_validation_valid = (
        "delivery proof client_label does not match revenue proof" in validation_text
        and "live-client proof client_label does not match revenue proof" in validation_text
        and "test_external_completion_artifact_discovery_rejects_inconsistent_revenue_references"
        in test_text
    )
    receipt_artifact_validation_evidence = [
        "runtime.ventureops.validation.discover_external_completion_artifacts",
        "runtime.ventureops.validation._validate_redacted_receipt_artifact",
        "runtime/ventureops/test_ventureops.py",
    ]
    receipt_artifact_validation_valid = (
        "receipt artifact invalid: {error}" in validation_text
        and "redacted must be true" in validation_text
        and "test_external_completion_artifact_discovery_rejects_invalid_receipt_artifact" in test_text
    )
    client_safe_delivery_artifact_validation_evidence = [
        "runtime.ventureops.validation.validate_client_safe_delivery_artifact",
        "runtime.ventureops.validation.discover_external_completion_artifacts",
        delivery_proof_packet_builder_module_rel,
        final_external_evidence_bundle_module_rel,
        "runtime/ventureops/test_ventureops.py",
    ]
    delivery_builder_text = _read_text_if_exists(root / delivery_proof_packet_builder_module_rel)
    final_bundle_text = _read_text_if_exists(root / final_external_evidence_bundle_module_rel)
    client_safe_delivery_artifact_validation_valid = (
        "def validate_client_safe_delivery_artifact" in validation_text
        and "client-safe delivery artifact invalid: {error}" in validation_text
        and "client_safe_delivery_artifact_validation" in delivery_builder_text
        and "client_safe_delivery_artifact_valid" in final_bundle_text
        and "test_external_completion_artifact_discovery_rejects_invalid_client_safe_delivery_artifact" in test_text
        and "test_delivery_proof_packet_builder_rejects_invalid_client_safe_delivery_artifact" in test_text
        and "test_final_external_evidence_bundle_validation_rejects_invalid_client_safe_delivery_artifact" in test_text
    )
    readiness_report_evidence = [
        live_client_readiness_report_rel,
        live_revenue_readiness_report_rel,
    ]
    readiness_report_writeback_valid = (
        live_client_readiness_report.get("report_written") is True
        and live_client_readiness_report.get("readiness_status") == "blocked"
        and live_client_readiness_report.get("live_client_scope_proof_performed") is False
        and live_client_readiness_report.get("live_client_data_ingested") is False
        and live_revenue_readiness_report.get("report_written") is True
        and live_revenue_readiness_report.get("readiness_status") == "blocked"
        and live_revenue_readiness_report.get("revenue_claim_made") is False
        and live_revenue_readiness_report.get("payment_mutation_performed") is False
    )
    live_readiness_report_guard_evidence = [
        readiness_cli_rel,
        "runtime/ventureops/test_ventureops.py",
    ]
    live_readiness_report_write_guard_valid = (
        "_write_guarded_json_report" in cli_text
        and "report path already exists" in cli_text
        and "report_path escapes vault root" in cli_text
        and "fail-closed-if-live-client-proof-readiness-report-exists-or-escapes-vault-root" in command_contract
        and "fail-closed-if-live-revenue-proof-readiness-report-exists-or-escapes-vault-root" in command_contract
        and "test_live_readiness_cli_blocks_existing_report_paths_without_overwrite" in test_text
        and "test_live_readiness_cli_blocks_escaped_report_paths_without_traceback" in test_text
    )
    live_readiness_report_dated_default_valid = (
        "_ventureops-live-client-proof-readiness-report.json" in cli_text
        and "_ventureops-live-revenue-proof-readiness-report.json" in cli_text
        and "_default_proof_date()" in cli_text
        and "default-write:dated-live-client-proof-readiness-report-with---write-report" in command_contract
        and "default-write:dated-live-revenue-proof-readiness-report-with---write-report" in command_contract
        and "test_live_readiness_cli_write_report_defaults_to_dated_report_paths" in test_text
    )
    live_readiness_report_default_collision_guard_valid = (
        "_next_available_default_report_path" in cli_text
        and "default-write:collision-safe-suffixed-live-client-proof-readiness-report" in command_contract
        and "default-write:collision-safe-suffixed-live-revenue-proof-readiness-report" in command_contract
        and "test_live_readiness_cli_write_report_uses_collision_safe_default_paths" in test_text
    )
    external_readiness_audit_report_write_guard_evidence = [
        readiness_cli_rel,
        "runtime/ventureops/test_ventureops.py",
    ]
    external_readiness_audit_report_write_guard_valid = (
        "report path already exists" in cli_text
        and "report_path escapes vault root" in cli_text
        and "report_write_blocked" in cli_text
        and "fail-closed-if-external-readiness-audit-report-exists-or-escapes-vault-root" in command_contract
        and "test_external_readiness_audit_cli_blocks_existing_report_path_without_overwrite" in test_text
        and "test_external_readiness_audit_cli_blocks_escaped_report_path_without_traceback" in test_text
    )
    external_readiness_audit_report_dated_default_evidence = [
        readiness_cli_rel,
        "runtime/ventureops/test_ventureops.py",
    ]
    external_readiness_audit_report_dated_default_valid = (
        "_ventureops-external-readiness-audit-report.json" in cli_text
        and "_default_proof_date()" in cli_text
        and "default-write:dated-external-readiness-audit-report-with---write-report" in command_contract
        and "test_external_readiness_audit_cli_write_report_defaults_to_dated_report_path" in test_text
    )
    external_readiness_audit_report_default_collision_guard_evidence = [
        readiness_cli_rel,
        "runtime/ventureops/test_ventureops.py",
    ]
    external_readiness_audit_report_default_collision_guard_valid = (
        "_next_available_default_report_path" in cli_text
        and "while (vault_root / candidate).exists()" in cli_text
        and "default-write:collision-safe-suffixed-external-readiness-audit-report" in command_contract
        and "test_external_readiness_audit_cli_write_report_uses_collision_safe_default_path" in test_text
    )
    evidence_template_evidence = [
        scope_evidence_template_report_rel,
        revenue_evidence_template_report_rel,
    ]
    evidence_template_writeback_valid = (
        scope_evidence_template_report.get("type") == "ventureops-real-client-scope-evidence"
        and scope_evidence_template_report.get("template_only") is True
        and scope_evidence_template_report.get("approved_read_paths") == []
        and revenue_evidence_template_report.get("type") == "ventureops-live-revenue-evidence"
        and revenue_evidence_template_report.get("template_only") is True
        and float(revenue_evidence_template_report.get("amount") or 0) == 0.0
    )
    template_only_scope_probe = validate_real_client_scope_evidence(
        {
            "type": "ventureops-real-client-scope-evidence",
            "template_only": True,
            "client_approved_scope_id": "probe-scope",
            "client_label": "Probe Client",
            "approval_id": "probe-approval",
            "approval_status": "approved",
            "approved_read_paths": ["client_scopes/probe/redacted.md"],
            "redaction_policy": "client_safe_summary_only",
            "delivery_boundary": "no_external_delivery",
        }
    )
    template_only_revenue_probe = validate_live_revenue_evidence(
        {
            "type": "ventureops-live-revenue-evidence",
            "template_only": True,
            "revenue_proof_id": "probe-revenue",
            "workflow_id": "agent_runtime_governance_audit",
            "client_label": "Probe Client",
            "payment_reference_id": "payment-ref-probe",
            "payment_status": "received",
            "amount": "1.00",
            "currency": "USD",
            "receipt_artifact_path": "07_LOGS/Revenue-Proofs/probe-receipt.json",
            "delivery_proof_path": "07_LOGS/Workflow-Proofs/probe-delivery.json",
            "crm_reference_id": "crm-probe",
            "approval_id": "probe-revenue-approval",
            "revenue_recognition_boundary": "proof_only_no_accounting_claim",
        }
    )
    template_only_rejection_guard_valid = (
        template_only_scope_probe["ok"] is False
        and "template_only scope evidence cannot be used as real client scope proof" in template_only_scope_probe["errors"]
        and template_only_revenue_probe["ok"] is False
        and "template_only revenue evidence cannot be used as live revenue proof" in template_only_revenue_probe["errors"]
    )

    missing_requirements: list[str] = []
    errors: list[str] = []
    if not passover_valid:
        errors.append("canonical external readiness passover is missing or stale")
    if not handover_alias_valid:
        errors.append("external readiness handover alias is missing or stale")
    if not requested_handover_alias_valid:
        errors.append("requested external readiness handover alias is missing or stale")
    if not requested_handover_next_pass_valid:
        errors.append("requested VentureOps-externaal handover next pass is stale")
    if not requested_handover_scope_output_route_valid:
        errors.append("requested VentureOps-externaal handover scope output route is stale")
    if not proof_chain_valid:
        errors.append("live client scope contract proof chain is incomplete")
    if not live_client_proof_present:
        missing_requirements.append("live client workflow proof missing")
    if not live_revenue_proof_present:
        missing_requirements.append("live revenue workflow proof missing")
    if live_client_proof_present and live_revenue_proof_present and not final_bundle_validation_ready:
        missing_requirements.append("final evidence bundle validation missing")
    if not live_client_proof_present:
        next_required_real_use_pass = "ventureops-live-client-workflow-proof"
        next_guarded_command = "chaseos ventureops validate-scope-evidence --packet PATH --vault-root VAULT_ROOT --json"
        next_required_inputs = [
            "typed real-client scope approval artifact",
            "real client-approved scope evidence packet",
            "approved scope source files inside the vault root",
        ]
    elif not live_revenue_proof_present:
        next_required_real_use_pass = "ventureops-live-revenue-proof"
        next_guarded_command = (
            "chaseos ventureops live-revenue-proof-readiness "
            "--revenue-packet PATH --live-client-proof-path PATH --json"
        )
        next_required_inputs = [
            "redacted live revenue evidence packet",
            "valid live-client workflow proof artifact",
            "valid live-delivery proof artifact",
        ]
    elif not final_bundle_validation_ready:
        next_required_real_use_pass = "ventureops-final-evidence-bundle-validation"
        next_guarded_command = (
            "chaseos ventureops final-evidence-bundle --bundle PATH "
            "--write-report --report-path PATH --json"
        )
        next_required_inputs = [
            "final evidence bundle packet",
            "valid live-client workflow proof artifact",
            "valid live revenue proof artifact",
        ]
    else:
        next_required_real_use_pass = "complete"
        next_guarded_command = "chaseos ventureops feature-family-completion-audit --json"
        next_required_inputs = []

    checklist = [
        _checklist_item(
            "review VentureOps external readiness handover",
            "verified" if handover_alias_valid else "failed",
            [str(handover_rel).replace("\\", "/")] if handover_path.exists() else [],
            "Handover is an alias to the canonical passover and points to the next blocked guarded proof lane.",
        ),
        _checklist_item(
            "review requested VentureOps-externaal handover alias",
            "verified" if requested_handover_alias_valid else "failed",
            [str(requested_handover_rel).replace("\\", "/")] if requested_handover_path.exists() else [],
            "Typo-compatible alias exists for the exact operator-requested filename, points back to the canonical handover/passover, and names the guarded revenue proof readiness lane as the next real-use pass.",
        ),
        _checklist_item(
            "validate canonical passover",
            "verified" if passover_valid else "failed",
            [str(passover_rel).replace("\\", "/")] if passover_path.exists() else [],
            "Passover lists verified external-readiness lanes and completion blockers.",
        ),
        _checklist_item(
            "TDD-backed implementation evidence",
            "verified" if tdd_verified else "failed",
            [path for path in tdd_evidence if (root / path).exists()],
            "Focused tests and build log document red -> green -> truth-sync for the current pass.",
        ),
        _checklist_item(
            "live client scope contract proof chain",
            "verified" if proof_chain_valid else "failed",
            existing_artifacts,
            "Bounded local AOR proof artifacts exist for the blocker contract lane.",
        ),
        _checklist_item(
            "real client scope evidence contract",
            "verified" if scope_contract_verified else "failed",
            scope_contract_evidence if scope_contract_verified else [],
            "Scope packet schema/template/validator exist and require a matching typed approval artifact; this does not prove a live client workflow.",
        ),
        _checklist_item(
            "real client scope approval artifact contract",
            "verified" if scope_approval_contract_verified else "failed",
            scope_approval_contract_evidence if scope_approval_contract_verified else [],
            "Typed scope approval schema/template/validator exist so arbitrary files cannot stand in for operator approval.",
        ),
        _checklist_item(
            "live revenue evidence contract",
            "verified" if revenue_contract_verified else "failed",
            revenue_contract_evidence if revenue_contract_verified else [],
            "Revenue packet schema/template/validator exist; this does not prove live revenue.",
        ),
        _checklist_item(
            "live client proof readiness CLI",
            "verified" if readiness_contract_verified else "failed",
            readiness_contract_evidence if readiness_contract_verified else [],
            "Readiness CLI checks whether a valid scope packet can proceed to the proof gate; this does not prove a live client workflow.",
        ),
        _checklist_item(
            "live revenue proof readiness CLI",
            "verified" if revenue_readiness_contract_verified else "failed",
            revenue_readiness_contract_evidence if revenue_readiness_contract_verified else [],
            "Revenue readiness CLI checks evidence and live-client proof prerequisites; this does not prove live revenue.",
        ),
        _checklist_item(
            "operator evidence intake CLI",
            "verified" if evidence_intake_cli_valid else "failed",
            evidence_intake_cli_evidence if evidence_intake_cli_valid else [],
            "Operator intake CLI composes scope/revenue packet validation and next-command routing; it does not run live client or revenue workflows.",
        ),
        _checklist_item(
            "evidence intake report write guard",
            "verified" if evidence_intake_report_write_guard_valid else "failed",
            evidence_intake_report_write_guard_evidence if evidence_intake_report_write_guard_valid else [],
            "Evidence intake report writeback blocks existing report paths and escaped report paths before blocked-state report writeback.",
        ),
        _checklist_item(
            "evidence intake report dated default",
            "verified" if evidence_intake_report_dated_default_valid else "failed",
            evidence_intake_report_dated_default_evidence if evidence_intake_report_dated_default_valid else [],
            "Evidence intake report writeback uses a date-stamped report path under `07_LOGS/Workflow-Proofs/` when no explicit report path is supplied.",
        ),
        _checklist_item(
            "evidence intake report default collision guard",
            "verified" if evidence_intake_report_default_collision_guard_valid else "failed",
            evidence_intake_report_default_collision_guard_evidence
            if evidence_intake_report_default_collision_guard_valid
            else [],
            "Evidence intake report writeback chooses the next available date-stamped default path when the base default already exists.",
        ),
        _checklist_item(
            "evidence discovery preflight CLI",
            "verified" if evidence_discovery_preflight_cli_valid else "failed",
            evidence_discovery_preflight_cli_evidence if evidence_discovery_preflight_cli_valid else [],
            "Discovery CLI scans bounded repo-local evidence roots, rejects template-only scaffolds, classifies scope-gate artifacts as insufficient for revenue, and does not execute live workflows.",
        ),
        _checklist_item(
            "real-client input manifest CLI",
            "verified" if real_client_input_manifest_cli_valid else "failed",
            real_client_input_manifest_cli_evidence if real_client_input_manifest_cli_valid else [],
            "Manifest CLI checks exact operator-supplied real-client scope inputs and recommends the next scope approval or scope packet command; it does not run live workflows.",
        ),
        _checklist_item(
            "real-client input manifest report write guard",
            "verified" if real_client_input_manifest_report_write_guard_valid else "failed",
            real_client_input_manifest_report_write_guard_evidence
            if real_client_input_manifest_report_write_guard_valid
            else [],
            "Real-client input manifest report writeback blocks existing report paths and escaped report paths, while omitted report paths use the next available dated default.",
        ),
        _checklist_item(
            "real-client input manifest report dated default",
            "verified" if real_client_input_manifest_report_dated_default_valid else "failed",
            real_client_input_manifest_report_dated_default_evidence
            if real_client_input_manifest_report_dated_default_valid
            else [],
            "Real-client input manifest report writeback uses a date-stamped report path under `07_LOGS/Workflow-Proofs/` when no explicit report path is supplied.",
        ),
        _checklist_item(
            "real-client input manifest report default collision guard",
            "verified" if real_client_input_manifest_report_default_collision_guard_valid else "failed",
            real_client_input_manifest_report_default_collision_guard_evidence
            if real_client_input_manifest_report_default_collision_guard_valid
            else [],
            "Real-client input manifest report writeback chooses the next available date-stamped default path when the base default already exists.",
        ),
        _checklist_item(
            "scope approval packet builder CLI",
            "verified" if scope_approval_packet_builder_cli_valid else "failed",
            scope_approval_packet_builder_cli_evidence if scope_approval_packet_builder_cli_valid else [],
            "Builder CLI writes a typed no-side-effect operator approval artifact for real-client scope evidence and does not run live workflows.",
        ),
        _checklist_item(
            "scope evidence packet builder CLI",
            "verified" if scope_evidence_packet_builder_cli_valid else "failed",
            scope_evidence_packet_builder_cli_evidence if scope_evidence_packet_builder_cli_valid else [],
            "Builder CLI writes a scope evidence packet only from a valid typed operator approval artifact plus approved source fields and does not run live workflows or make completion claims.",
        ),
        _checklist_item(
            "revenue evidence packet builder CLI",
            "verified" if revenue_evidence_packet_builder_cli_valid else "failed",
            revenue_evidence_packet_builder_cli_evidence if revenue_evidence_packet_builder_cli_valid else [],
            "Builder CLI writes a revenue evidence packet only from operator-supplied receipt/delivery/proof fields and does not run live workflows, mutate payment/CRM systems, or make revenue claims.",
        ),
        _checklist_item(
            "delivery proof packet builder CLI",
            "verified" if delivery_proof_packet_builder_cli_valid else "failed",
            delivery_proof_packet_builder_cli_evidence if delivery_proof_packet_builder_cli_valid else [],
            "Builder CLI writes an operator-attested delivery proof artifact and does not perform external delivery, CRM/payment mutation, invoice send, provider/browser action, or revenue claims.",
        ),
        _checklist_item(
            "external packet output collision guard",
            "verified" if external_packet_output_collision_guard_valid else "failed",
            external_packet_output_collision_guard_evidence if external_packet_output_collision_guard_valid else [],
            "External evidence packet builders fail closed on existing output paths so prior operator artifacts are not silently overwritten.",
        ),
        _checklist_item(
            "external packet path guard",
            "verified" if external_packet_path_guard_valid else "failed",
            external_packet_path_guard_evidence if external_packet_path_guard_valid else [],
            "External evidence packet builders return structured blocked results for escaped paths instead of raising or writing outside the vault root.",
        ),
        _checklist_item(
            "real evidence closeout readiness CLI",
            "verified" if real_evidence_closeout_readiness_cli_valid else "failed",
            real_evidence_closeout_cli_evidence if real_evidence_closeout_readiness_cli_valid else [],
            "Closeout CLI reviews the typo handover, canonical passover, audit, and intake state; it does not mark VentureOps complete without real external proof.",
        ),
        _checklist_item(
            "real evidence closeout report write guard",
            "verified" if real_evidence_closeout_report_write_guard_valid else "failed",
            real_evidence_closeout_report_write_guard_evidence
            if real_evidence_closeout_report_write_guard_valid
            else [],
            "Real evidence closeout report writeback blocks existing report paths and escaped report paths so closeout handoff reports cannot overwrite prior reports or be written outside the vault root.",
        ),
        _checklist_item(
            "real evidence closeout report dated default",
            "verified" if real_evidence_closeout_report_dated_default_valid else "failed",
            real_evidence_closeout_report_dated_default_evidence
            if real_evidence_closeout_report_dated_default_valid
            else [],
            "Real evidence closeout report writeback defaults to a date-stamped report path under `07_LOGS/Workflow-Proofs/` when no explicit report path is supplied.",
        ),
        _checklist_item(
            "real evidence closeout report default collision guard",
            "verified" if real_evidence_closeout_report_default_collision_guard_valid else "failed",
            real_evidence_closeout_report_default_collision_guard_evidence
            if real_evidence_closeout_report_default_collision_guard_valid
            else [],
            "Real evidence closeout report writeback chooses the next available date-stamped default path when the base default already exists.",
        ),
        _checklist_item(
            "whole feature-family completion audit CLI",
            "verified" if feature_family_completion_audit_cli_valid else "failed",
            feature_family_completion_audit_cli_evidence if feature_family_completion_audit_cli_valid else [],
            "Feature-family audit maps the full VentureOps objective to concrete artifacts and refuses completion while external proof is missing.",
        ),
        _checklist_item(
            "feature-family completion audit report write guard",
            "verified" if feature_family_completion_audit_report_write_guard_valid else "failed",
            feature_family_completion_audit_report_write_guard_evidence
            if feature_family_completion_audit_report_write_guard_valid
            else [],
            "Feature-family completion audit report writeback blocks existing report paths and escaped report paths so final closeout reports cannot overwrite prior reports or be written outside the vault root.",
        ),
        _checklist_item(
            "feature-family completion audit report dated default",
            "verified" if feature_family_completion_audit_report_dated_default_valid else "failed",
            feature_family_completion_audit_report_dated_default_evidence
            if feature_family_completion_audit_report_dated_default_valid
            else [],
            "Feature-family completion audit report writeback defaults to a date-stamped report path under `07_LOGS/Workflow-Proofs/` when no explicit report path is supplied.",
        ),
        _checklist_item(
            "feature-family completion audit report default collision guard",
            "verified" if feature_family_completion_audit_report_default_collision_guard_valid else "failed",
            feature_family_completion_audit_report_default_collision_guard_evidence
            if feature_family_completion_audit_report_default_collision_guard_valid
            else [],
            "Feature-family completion audit report writeback chooses the next available date-stamped default path when the base default already exists.",
        ),
        _checklist_item(
            "final external execution runbook CLI",
            "verified" if final_external_execution_runbook_cli_valid else "failed",
            final_external_execution_runbook_cli_evidence if final_external_execution_runbook_cli_valid else [],
            "Runbook CLI turns the final external passover into an ordered command sequence, includes final evidence bundle packet authoring and validation before final audit rerun, and does not execute live workflows or make completion claims.",
        ),
        _checklist_item(
            "final external runbook report write guard",
            "verified" if final_external_runbook_report_write_guard_valid else "failed",
            final_external_runbook_report_write_guard_evidence
            if final_external_runbook_report_write_guard_valid
            else [],
            "Final external runbook report writeback blocks existing report paths and escaped report paths so blocked-state runbook reports cannot overwrite prior reports or be written outside the vault root.",
        ),
        _checklist_item(
            "final external runbook report dated default",
            "verified" if final_external_runbook_report_dated_default_valid else "failed",
            final_external_runbook_report_dated_default_evidence
            if final_external_runbook_report_dated_default_valid
            else [],
            "Final external runbook report writeback defaults to a date-stamped report path under `07_LOGS/Workflow-Proofs/` when no explicit report path is supplied.",
        ),
        _checklist_item(
            "final external runbook report default collision guard",
            "verified" if final_external_runbook_report_default_collision_guard_valid else "failed",
            final_external_runbook_report_default_collision_guard_evidence
            if final_external_runbook_report_default_collision_guard_valid
            else [],
            "Final external runbook report writeback chooses the next available date-stamped default path when the base default already exists.",
        ),
        _checklist_item(
            "final external evidence bundle validator",
            "verified" if final_evidence_bundle_validator_valid else "failed",
            final_evidence_bundle_validator_evidence if final_evidence_bundle_validator_valid else [],
            "Validator checks the whole proof chain in one operator-supplied bundle before the final completion audit is rerun.",
        ),
        _checklist_item(
            "final evidence bundle validation report write guard",
            "verified" if final_evidence_bundle_validation_report_write_guard_valid else "failed",
            final_evidence_bundle_validation_report_write_guard_evidence
            if final_evidence_bundle_validation_report_write_guard_valid
            else [],
            "Final bundle validation report writeback blocks existing report paths and escaped report paths so final completion evidence cannot overwrite prior reports or be written outside the vault root.",
        ),
        _checklist_item(
            "final evidence bundle validation report dated default",
            "verified" if final_evidence_bundle_validation_report_dated_default_valid else "failed",
            final_evidence_bundle_validation_report_dated_default_evidence
            if final_evidence_bundle_validation_report_dated_default_valid
            else [],
            "Final bundle validation report writeback defaults to a date-stamped report path under `07_LOGS/Workflow-Proofs/` when no explicit report path is supplied.",
        ),
        _checklist_item(
            "final evidence bundle validation report default collision guard",
            "verified" if final_evidence_bundle_validation_report_default_collision_guard_valid else "failed",
            final_evidence_bundle_validation_report_default_collision_guard_evidence
            if final_evidence_bundle_validation_report_default_collision_guard_valid
            else [],
            "Final bundle validation report writeback chooses the next available date-stamped default path when the base default already exists.",
        ),
        _checklist_item(
            "final evidence bundle packet builder CLI",
            "verified" if final_evidence_bundle_packet_builder_cli_valid else "failed",
            final_evidence_bundle_packet_builder_evidence if final_evidence_bundle_packet_builder_cli_valid else [],
            "Builder writes the final evidence bundle envelope from existing proof paths and does not execute live workflows or create proof evidence.",
        ),
        _checklist_item(
            "final evidence bundle packet path guard",
            "verified" if final_evidence_bundle_packet_path_guard_valid else "failed",
            final_evidence_bundle_packet_path_guard_evidence
            if final_evidence_bundle_packet_path_guard_valid
            else [],
            "Builder returns structured blocked results for escaped final bundle packet paths instead of raising or writing outside the vault root.",
        ),
        _checklist_item(
            "final evidence bundle report reference revalidation",
            "verified" if final_evidence_bundle_report_reference_revalidation_valid else "failed",
            final_evidence_bundle_report_reference_revalidation_evidence
            if final_evidence_bundle_report_reference_revalidation_valid
            else [],
            "Completion discovery revalidates each report's referenced bundle before accepting a ready final evidence bundle validation report.",
        ),
        _checklist_item(
            "final evidence bundle validation report",
            "verified"
            if final_bundle_validation_ready
            else ("missing" if live_client_proof_present and live_revenue_proof_present else "blocked"),
            final_bundle_validation_reports["valid_final_evidence_bundle_validation_reports"],
            "Requires a ready `final-evidence-bundle` validation report that matches the currently valid live-client and live-revenue proof artifacts before the final completion audit can pass.",
        ),
        _checklist_item(
            "scope evidence source path verifier",
            "verified" if scope_source_path_verifier_valid else "failed",
            scope_source_path_verifier_evidence if scope_source_path_verifier_valid else [],
            "Verifier checks that approved scope read paths exist as files before the scope proof gate is reported ready; this prevents missing approved read paths from being reported ready.",
        ),
        _checklist_item(
            "live client proof artifact verifier",
            "verified" if live_client_proof_artifact_verifier_valid else "failed",
            live_client_proof_artifact_verifier_evidence if live_client_proof_artifact_verifier_valid else [],
            "Verifier checks live-client proof artifact shape and boundary flags, which prevents arbitrary files from satisfying the revenue prerequisite.",
        ),
        _checklist_item(
            "live delivery proof artifact verifier",
            "verified" if live_delivery_proof_artifact_verifier_valid else "failed",
            live_delivery_proof_artifact_verifier_evidence if live_delivery_proof_artifact_verifier_valid else [],
            "Verifier checks redacted operator-attested delivery proof shape and boundary flags, which prevents arbitrary delivery files from satisfying the revenue prerequisite.",
        ),
        _checklist_item(
            "guarded live client scope proof CLI",
            "verified" if live_client_scope_proof_cli_valid else "failed",
            live_client_scope_proof_cli_evidence if live_client_scope_proof_cli_valid else [],
            "Guarded CLI can execute the local AOR proof gate only with explicit --execute-proof and a valid scope packet; it does not prove a completed live client workflow until real scope evidence is run.",
        ),
        _checklist_item(
            "guarded live client workflow proof CLI",
            "verified" if live_client_workflow_proof_cli_valid else "failed",
            live_client_workflow_proof_cli_evidence if live_client_workflow_proof_cli_valid else [],
            "Guarded CLI can write a scoped local live-client workflow proof after explicit --execute-proof and valid scope/source evidence; it does not prove a completed live client workflow until real scope evidence is run.",
        ),
        _checklist_item(
            "guarded live revenue proof CLI",
            "verified" if live_revenue_proof_cli_valid else "failed",
            live_revenue_proof_cli_evidence if live_revenue_proof_cli_valid else [],
            "Guarded CLI can write proof-only local revenue evidence after explicit --execute-proof and valid packet/prerequisite artifacts; it does not create an accounting claim or complete live revenue.",
        ),
        _checklist_item(
            "guarded proof output collision guard",
            "verified" if guarded_proof_output_collision_guard_valid else "failed",
            guarded_proof_output_collision_guard_evidence if guarded_proof_output_collision_guard_valid else [],
            "Guarded proof commands fail closed on existing proof output paths so final proof artifacts are not silently overwritten.",
        ),
        _checklist_item(
            "revenue completion reference revalidation",
            "verified" if revenue_completion_reference_revalidation_valid else "failed",
            revenue_completion_reference_revalidation_evidence
            if revenue_completion_reference_revalidation_valid
            else [],
            "Completion discovery revalidates referenced receipt, delivery proof, and client-safe delivery artifacts from disk before accepting proof-only revenue completion.",
        ),
        _checklist_item(
            "live-revenue packet reference revalidation",
            "verified" if live_revenue_packet_reference_revalidation_valid else "failed",
            live_revenue_packet_reference_revalidation_evidence
            if live_revenue_packet_reference_revalidation_valid
            else [],
            "Completion discovery revalidates the referenced revenue packet from disk before accepting proof-only revenue completion.",
        ),
        _checklist_item(
            "live-client workflow source digest validation",
            "verified" if live_client_source_digest_validation_valid else "failed",
            live_client_source_digest_validation_evidence if live_client_source_digest_validation_valid else [],
            "Live-client workflow proof validation requires source_digests must cover approved_read_paths before a final proof artifact can satisfy completion.",
        ),
        _checklist_item(
            "live-client completion reference revalidation",
            "verified" if live_client_completion_reference_revalidation_valid else "failed",
            live_client_completion_reference_revalidation_evidence
            if live_client_completion_reference_revalidation_valid
            else [],
            "Completion discovery revalidates referenced scope proof gate, client report, and scorecard artifacts from disk before accepting live-client workflow completion.",
        ),
        _checklist_item(
            "live-client scope packet reference revalidation",
            "verified" if live_client_scope_packet_reference_revalidation_valid else "failed",
            live_client_scope_packet_reference_revalidation_evidence
            if live_client_scope_packet_reference_revalidation_valid
            else [],
            "Completion discovery revalidates the referenced scope packet, approval artifact, and approved source files from disk before accepting live-client workflow completion.",
        ),
        _checklist_item(
            "live-client reference consistency validation",
            "verified" if live_client_reference_consistency_validation_valid else "failed",
            live_client_reference_consistency_validation_evidence
            if live_client_reference_consistency_validation_valid
            else [],
            "Completion discovery verifies referenced scope proof gate and scorecard artifacts match the live-client workflow proof scope, approval, read paths, workflow id, and run id.",
        ),
        _checklist_item(
            "revenue reference consistency validation",
            "verified" if revenue_reference_consistency_validation_valid else "failed",
            revenue_reference_consistency_validation_evidence
            if revenue_reference_consistency_validation_valid
            else [],
            "Completion discovery verifies referenced delivery and live-client proof artifacts match the proof-only revenue artifact workflow id and client label.",
        ),
        _checklist_item(
            "receipt artifact validation",
            "verified" if receipt_artifact_validation_valid else "failed",
            receipt_artifact_validation_evidence if receipt_artifact_validation_valid else [],
            "Completion discovery validates referenced receipt artifacts are JSON objects marked redacted before accepting proof-only revenue completion.",
        ),
        _checklist_item(
            "client-safe delivery artifact validation",
            "verified" if client_safe_delivery_artifact_validation_valid else "failed",
            client_safe_delivery_artifact_validation_evidence
            if client_safe_delivery_artifact_validation_valid
            else [],
            "Delivery proof authoring, final completion discovery, and final bundle validation require the referenced client-safe delivery artifact to be redacted JSON with no side-effect or secret-shaped fields.",
        ),
        _checklist_item(
            "live readiness report writeback",
            "verified" if readiness_report_writeback_valid else "failed",
            readiness_report_evidence if readiness_report_writeback_valid else [],
            "Readiness report writeback is a blocked-state operator passover artifact and does not prove live client or live revenue completion.",
        ),
        _checklist_item(
            "live readiness report write guard",
            "verified" if live_readiness_report_write_guard_valid else "failed",
            live_readiness_report_guard_evidence if live_readiness_report_write_guard_valid else [],
            "Live client and live revenue readiness report writeback blocks existing report paths and escaped report paths before blocked-state report writeback.",
        ),
        _checklist_item(
            "live readiness report dated default",
            "verified" if live_readiness_report_dated_default_valid else "failed",
            live_readiness_report_guard_evidence if live_readiness_report_dated_default_valid else [],
            "Live client and live revenue readiness report writeback uses date-stamped report paths under `07_LOGS/Workflow-Proofs/` when no explicit report path is supplied.",
        ),
        _checklist_item(
            "live readiness report default collision guard",
            "verified" if live_readiness_report_default_collision_guard_valid else "failed",
            live_readiness_report_guard_evidence if live_readiness_report_default_collision_guard_valid else [],
            "Live client and live revenue readiness report writeback chooses the next available date-stamped default path when the base default already exists.",
        ),
        _checklist_item(
            "external readiness audit report write guard",
            "verified" if external_readiness_audit_report_write_guard_valid else "failed",
            external_readiness_audit_report_write_guard_evidence
            if external_readiness_audit_report_write_guard_valid
            else [],
            "External readiness audit report writeback blocks existing report paths and escaped report paths so blocked-state audit reports cannot overwrite prior reports or be written outside the vault root.",
        ),
        _checklist_item(
            "external readiness audit report dated default",
            "verified" if external_readiness_audit_report_dated_default_valid else "failed",
            external_readiness_audit_report_dated_default_evidence
            if external_readiness_audit_report_dated_default_valid
            else [],
            "External readiness audit report writeback defaults to a date-stamped report path under `07_LOGS/Workflow-Proofs/` when no explicit report path is supplied.",
        ),
        _checklist_item(
            "external readiness audit report default collision guard",
            "verified" if external_readiness_audit_report_default_collision_guard_valid else "failed",
            external_readiness_audit_report_default_collision_guard_evidence
            if external_readiness_audit_report_default_collision_guard_valid
            else [],
            "External readiness audit report writeback chooses the next available date-stamped default path when the base default already exists.",
        ),
        _checklist_item(
            "external evidence packet templates",
            "verified" if evidence_template_writeback_valid else "failed",
            evidence_template_evidence if evidence_template_writeback_valid else [],
            "Evidence packet template writeback is operator input scaffolding and does not prove live client or live revenue completion.",
        ),
        _checklist_item(
            "template-only evidence rejection guard",
            "verified" if template_only_rejection_guard_valid else "failed",
            [
                "runtime.ventureops.validation.validate_real_client_scope_evidence",
                "runtime.ventureops.validation.validate_live_revenue_evidence",
            ]
            if template_only_rejection_guard_valid
            else [],
            "Validator self-check proves template-only scaffolds cannot be accepted as proof.",
        ),
        _checklist_item(
            "actual final proof artifact discovery",
            "verified",
            [
                "runtime.ventureops.validation.discover_external_completion_artifacts",
                "runtime.ventureops.validation.validate_live_client_workflow_proof_artifact",
                "runtime.ventureops.validation.validate_live_revenue_proof_artifact",
            ],
            "Completion audit requires actual valid live-client workflow and proof-only revenue artifacts. Synthetic scorecard metrics alone cannot clear final completion.",
        ),
        _checklist_item(
            "live client workflow",
            "verified" if live_client_proof_present else "missing",
            external_completion_artifacts["valid_live_client_workflow_proof_artifacts"],
            "Requires an actual valid ventureops-live-client-workflow-proof artifact written from real client-approved scope evidence.",
        ),
        _checklist_item(
            "live revenue workflow",
            "verified" if live_revenue_proof_present else "missing",
            external_completion_artifacts["valid_live_revenue_proof_artifacts"],
            "Requires an actual valid ventureops-live-revenue-proof artifact that references a valid live-client workflow proof artifact.",
        ),
        _checklist_item(
            "full VentureOps feature family complete",
            "verified"
            if live_client_proof_present and live_revenue_proof_present and final_bundle_validation_ready
            else "blocked",
            [],
            "Blocked until all required live-client, live-revenue, and final evidence bundle validation evidence exists.",
        ),
    ]

    complete = not errors and not missing_requirements
    return {
        "ok": not errors,
        "complete": complete,
        "completion_decision": "complete" if complete else "not_complete",
        "status": current_status,
        "passover_path": str(passover_rel).replace("\\", "/"),
        "handover_path": str(handover_rel).replace("\\", "/"),
        "requested_handover_path": str(requested_handover_rel).replace("\\", "/"),
        "handover_alias_valid": handover_alias_valid,
        "requested_handover_alias_valid": requested_handover_alias_valid,
        "requested_handover_next_pass_valid": requested_handover_next_pass_valid,
        "requested_handover_scope_output_route_valid": requested_handover_scope_output_route_valid,
        "passover_valid": passover_valid,
        "readiness_report_writeback_valid": readiness_report_writeback_valid,
        "live_readiness_report_write_guard_valid": live_readiness_report_write_guard_valid,
        "live_readiness_report_dated_default_valid": live_readiness_report_dated_default_valid,
        "live_readiness_report_default_collision_guard_valid": (
            live_readiness_report_default_collision_guard_valid
        ),
        "external_readiness_audit_report_write_guard_valid": external_readiness_audit_report_write_guard_valid,
        "external_readiness_audit_report_dated_default_valid": external_readiness_audit_report_dated_default_valid,
        "external_readiness_audit_report_default_collision_guard_valid": (
            external_readiness_audit_report_default_collision_guard_valid
        ),
        "evidence_template_writeback_valid": evidence_template_writeback_valid,
        "template_only_rejection_guard_valid": template_only_rejection_guard_valid,
        "evidence_intake_cli_valid": evidence_intake_cli_valid,
        "evidence_intake_report_write_guard_valid": evidence_intake_report_write_guard_valid,
        "evidence_intake_report_dated_default_valid": evidence_intake_report_dated_default_valid,
        "evidence_intake_report_default_collision_guard_valid": (
            evidence_intake_report_default_collision_guard_valid
        ),
        "evidence_discovery_preflight_cli_valid": evidence_discovery_preflight_cli_valid,
        "real_client_input_manifest_cli_valid": real_client_input_manifest_cli_valid,
        "real_client_input_manifest_report_write_guard_valid": real_client_input_manifest_report_write_guard_valid,
        "real_client_input_manifest_report_dated_default_valid": (
            real_client_input_manifest_report_dated_default_valid
        ),
        "real_client_input_manifest_report_default_collision_guard_valid": (
            real_client_input_manifest_report_default_collision_guard_valid
        ),
        "scope_approval_contract_verified": scope_approval_contract_verified,
        "scope_approval_packet_builder_cli_valid": scope_approval_packet_builder_cli_valid,
        "scope_evidence_packet_builder_cli_valid": scope_evidence_packet_builder_cli_valid,
        "revenue_evidence_packet_builder_cli_valid": revenue_evidence_packet_builder_cli_valid,
        "delivery_proof_packet_builder_cli_valid": delivery_proof_packet_builder_cli_valid,
        "external_packet_output_collision_guard_valid": external_packet_output_collision_guard_valid,
        "external_packet_path_guard_valid": external_packet_path_guard_valid,
        "real_evidence_closeout_readiness_cli_valid": real_evidence_closeout_readiness_cli_valid,
        "real_evidence_closeout_report_write_guard_valid": real_evidence_closeout_report_write_guard_valid,
        "real_evidence_closeout_report_dated_default_valid": real_evidence_closeout_report_dated_default_valid,
        "real_evidence_closeout_report_default_collision_guard_valid": (
            real_evidence_closeout_report_default_collision_guard_valid
        ),
        "feature_family_completion_audit_cli_valid": feature_family_completion_audit_cli_valid,
        "feature_family_completion_audit_report_write_guard_valid": (
            feature_family_completion_audit_report_write_guard_valid
        ),
        "feature_family_completion_audit_report_dated_default_valid": (
            feature_family_completion_audit_report_dated_default_valid
        ),
        "feature_family_completion_audit_report_default_collision_guard_valid": (
            feature_family_completion_audit_report_default_collision_guard_valid
        ),
        "final_external_execution_runbook_cli_valid": final_external_execution_runbook_cli_valid,
        "final_external_runbook_report_write_guard_valid": final_external_runbook_report_write_guard_valid,
        "final_external_runbook_report_dated_default_valid": final_external_runbook_report_dated_default_valid,
        "final_external_runbook_report_default_collision_guard_valid": (
            final_external_runbook_report_default_collision_guard_valid
        ),
        "final_evidence_bundle_validator_valid": final_evidence_bundle_validator_valid,
        "final_evidence_bundle_validation_report_write_guard_valid": (
            final_evidence_bundle_validation_report_write_guard_valid
        ),
        "final_evidence_bundle_validation_report_dated_default_valid": (
            final_evidence_bundle_validation_report_dated_default_valid
        ),
        "final_evidence_bundle_validation_report_default_collision_guard_valid": (
            final_evidence_bundle_validation_report_default_collision_guard_valid
        ),
        "final_evidence_bundle_packet_builder_cli_valid": final_evidence_bundle_packet_builder_cli_valid,
        "final_evidence_bundle_packet_path_guard_valid": final_evidence_bundle_packet_path_guard_valid,
        "final_evidence_bundle_report_reference_revalidation_valid": (
            final_evidence_bundle_report_reference_revalidation_valid
        ),
        "scope_source_path_verifier_valid": scope_source_path_verifier_valid,
        "live_client_proof_artifact_verifier_valid": live_client_proof_artifact_verifier_valid,
        "live_delivery_proof_artifact_verifier_valid": live_delivery_proof_artifact_verifier_valid,
        "external_completion_artifact_discovery_valid": external_completion_artifact_discovery_valid,
        "final_evidence_bundle_validation_report_present": bool(
            final_bundle_validation_reports["final_evidence_bundle_validation_report_present"]
        ),
        "final_evidence_bundle_validation_ready": final_bundle_validation_ready,
        "final_evidence_bundle_validation_reports": final_bundle_validation_reports,
        "live_client_scope_proof_cli_valid": live_client_scope_proof_cli_valid,
        "live_client_workflow_proof_cli_valid": live_client_workflow_proof_cli_valid,
        "live_revenue_proof_cli_valid": live_revenue_proof_cli_valid,
        "guarded_proof_output_collision_guard_valid": guarded_proof_output_collision_guard_valid,
        "revenue_completion_reference_revalidation_valid": revenue_completion_reference_revalidation_valid,
        "live_revenue_packet_reference_revalidation_valid": live_revenue_packet_reference_revalidation_valid,
        "live_client_source_digest_validation_valid": live_client_source_digest_validation_valid,
        "live_client_completion_reference_revalidation_valid": live_client_completion_reference_revalidation_valid,
        "live_client_scope_packet_reference_revalidation_valid": (
            live_client_scope_packet_reference_revalidation_valid
        ),
        "live_client_reference_consistency_validation_valid": live_client_reference_consistency_validation_valid,
        "revenue_reference_consistency_validation_valid": revenue_reference_consistency_validation_valid,
        "receipt_artifact_validation_valid": receipt_artifact_validation_valid,
        "client_safe_delivery_artifact_validation_valid": client_safe_delivery_artifact_validation_valid,
        "latest_aor_chain_prefix": LIVE_CLIENT_SCOPE_PREFIX,
        "proof_chain_artifact_count": len(existing_artifacts),
        "expected_proof_chain_artifact_count": len(expected_artifacts),
        "live_client_scope_contract": contract,
        "scorecard_metrics": metrics,
        "external_completion_artifacts": external_completion_artifacts,
        "next_required_real_use_pass": next_required_real_use_pass,
        "next_guarded_command": next_guarded_command,
        "next_required_inputs": next_required_inputs,
        "missing_requirements": missing_requirements,
        "errors": errors,
        "prompt_to_artifact_checklist": checklist,
    }
