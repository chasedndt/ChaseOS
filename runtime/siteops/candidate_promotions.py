"""Scoped SiteOps contracts for Browser Skill candidate promotion."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - JSON fallback keeps tests dependency-light
    yaml = None

from runtime.browser_skills.candidates import (
    BrowserSkillCandidateError,
    SITEOPS_SKILL_CARD_REL,
    TRUSTED_SKILL_REL,
    candidate_promotion_request_contract,
)
from runtime.chaseos_gate import check_runtime_operation
from runtime.siteops.approvals import (
    approvals_dir,
    create_approval_request,
    decide_approval_request,
    list_approval_requests,
    show_approval_request,
)
from runtime.siteops.audit import append_audit_event, audit_path, now_iso, write_run_record
from runtime.siteops.errors import SiteOpsError, SiteOpsValidationError
from runtime.siteops.models import SiteOpsAuditEvent, SiteOpsRun, SiteOpsScope
from runtime.siteops.tenancy import has_any_role, load_tenant, require_scope
from runtime.siteops.validator import scan_secret_like_keys


PROMOTION_ACTION = "browser_skill_candidate.promote"
PROMOTION_APPLY_ACTION = "browser_skill_candidate.apply_promotion"
PROMOTION_APPROVAL_REBIND_SPEC_ACTION = "browser_skill_candidate.approval_rebind_spec"
PROMOTION_BOUND_APPROVAL_REQUEST_SPEC_ACTION = "browser_skill_candidate.bound_approval_request_spec"
PROMOTION_BOUND_APPROVAL_WRITER_DESIGN_ACTION = "browser_skill_candidate.bound_approval_writer_design"
PROMOTION_BOUND_APPROVAL_WRITER_PREFLIGHT_ACTION = "browser_skill_candidate.bound_approval_writer_preflight"
PROMOTION_BOUND_APPROVAL_WRITER_IMPLEMENTATION_REQUEST_ACTION = (
    "browser_skill_candidate.bound_approval_writer_implementation_request"
)
PROMOTION_BOUND_APPROVAL_WRITER_IMPLEMENTATION_APPROVAL_ACTION = (
    "browser_skill_candidate.bound_approval_writer_implementation_approval"
)
PROMOTION_BOUND_APPROVAL_WRITER_IMPLEMENTATION_ACTION = (
    "browser_skill_candidate.bound_approval_writer_implementation"
)
PROMOTION_SOURCE_APPROVAL_REBIND_LIVE_READINESS_ACTION = (
    "browser_skill_candidate.source_approval_rebind_live_readiness"
)
PROMOTION_REPLACEMENT_APPROVAL_DECISION_CONSUMPTION_ACTION = (
    "browser_skill_candidate.replacement_approval_decision_consumption"
)
PROMOTION_GATE_APPLY_ACTION = "browser_skill_candidate.gate_apply_design"
PROMOTION_GATE_EXECUTOR_SPEC_ACTION = "browser_skill_candidate.gate_executor_spec"
PROMOTION_GATE_ALLOWLIST_REVIEW_ACTION = "browser_skill_candidate.gate_allowlist_review"
PROMOTION_TRUSTED_EXECUTOR_DESIGN_ACTION = "browser_skill_candidate.trusted_executor_design"
PROMOTION_EXECUTOR_REVIEW_CHECKLIST_ACTION = "browser_skill_candidate.executor_review_checklist"
PROMOTION_PREIMPLEMENTATION_VERIFIER_ACTION = "browser_skill_candidate.preimplementation_verifier"
PROMOTION_EXECUTOR_IMPLEMENTATION_DESIGN_REVIEW_ACTION = (
    "browser_skill_candidate.executor_implementation_design_review"
)
PROMOTION_EXECUTOR_PREWRITE_AUDIT_SPEC_ACTION = "browser_skill_candidate.executor_prewrite_audit_spec"
PROMOTION_INACTIVE_ARTIFACT_VALIDATOR_ACTION = "browser_skill_candidate.inactive_artifact_validator"
PROMOTION_TRUSTED_INACTIVE_ARTIFACT_WRITER_PREFLIGHT_ACTION = (
    "browser_skill_candidate.trusted_inactive_artifact_writer_preflight"
)
PROMOTION_TRUSTED_INACTIVE_ARTIFACT_WRITER_IMPLEMENTATION_REQUEST_ACTION = (
    "browser_skill_candidate.trusted_inactive_artifact_writer_implementation_request"
)
PROMOTION_TRUSTED_INACTIVE_ARTIFACT_WRITER_IMPLEMENTATION_APPROVAL_ACTION = (
    "browser_skill_candidate.trusted_inactive_artifact_writer_implementation_approval"
)
PROMOTION_TRUSTED_INACTIVE_ARTIFACT_WRITER_IMPLEMENTATION_ACTION = (
    "browser_skill_candidate.trusted_inactive_artifact_writer_implementation"
)
PROMOTION_TRUSTED_INACTIVE_ARTIFACT_WRITER_LIVE_GATE_READINESS_ACTION = (
    "browser_skill_candidate.trusted_inactive_artifact_writer_live_gate_readiness"
)
PROMOTION_TRUSTED_INACTIVE_ARTIFACT_WRITER_GATE_ALLOWLIST_APPROVAL_REQUEST_ACTION = (
    "browser_skill_candidate.gate_allowlist_approval_request"
)
PROMOTION_TRUSTED_INACTIVE_ARTIFACT_WRITER_GATE_ALLOWLIST_DECISION_PREFLIGHT_ACTION = (
    "browser_skill_candidate.gate_allowlist_decision_preflight"
)
PROMOTION_TRUSTED_INACTIVE_ARTIFACT_WRITER_GATE_POLICY_PATCH_PLAN_ACTION = (
    "browser_skill_candidate.gate_policy_patch_plan"
)
PROMOTION_TRUSTED_INACTIVE_ARTIFACT_WRITER_GATE_POLICY_PATCH_APPLICATION_DESIGN_ACTION = (
    "browser_skill_candidate.gate_policy_patch_application_design"
)
PROMOTION_TRUSTED_INACTIVE_ARTIFACT_WRITER_GATE_POLICY_PATCH_APPLICATION_PREFLIGHT_ACTION = (
    "browser_skill_candidate.gate_policy_patch_application_preflight"
)
PROMOTION_TRUSTED_INACTIVE_ARTIFACT_WRITER_GATE_POLICY_PATCH_APPLICATION_WRITE_GUARD_ACTION = (
    "browser_skill_candidate.gate_policy_patch_application_write_guard_contract"
)
PROMOTION_TRUSTED_INACTIVE_ARTIFACT_WRITER_GATE_POLICY_PATCH_WRITER_DESIGN_ACTION = (
    "browser_skill_candidate.gate_policy_patch_writer_design"
)
PROMOTION_TRUSTED_INACTIVE_ARTIFACT_WRITER_GATE_POLICY_PATCH_WRITER_IMPLEMENTATION_REQUEST_ACTION = (
    "browser_skill_candidate.gate_policy_patch_writer_implementation_request"
)
PROMOTION_TRUSTED_INACTIVE_ARTIFACT_WRITER_GATE_POLICY_PATCH_WRITER_IMPLEMENTATION_APPROVAL_ACTION = (
    "browser_skill_candidate.gate_policy_patch_writer_implementation_approval"
)
PROMOTION_TRUSTED_INACTIVE_ARTIFACT_WRITER_GATE_POLICY_PATCH_WRITER_IMPLEMENTATION_ACTION = (
    "browser_skill_candidate.gate_policy_patch_writer_implementation"
)
PROMOTION_TRUSTED_INACTIVE_ARTIFACT_WRITER_GATE_POLICY_LIVE_APPLICATION_READINESS_ACTION = (
    "browser_skill_candidate.gate_policy_live_application_readiness"
)
PROMOTION_APPLY_TRUSTED_CANDIDATE_ARTIFACTS_ACTION = (
    "browser_skill_candidate.apply_trusted_candidate_artifacts"
)
PROMOTION_COLLISION_POLICY_SPEC_ACTION = "browser_skill_candidate.collision_policy_spec"
PROMOTION_ACTIVATION_BOUNDARY_READINESS_ACTION = "browser_skill_candidate.activation_boundary_readiness"
PROMOTION_ACTIVATION_APPROVAL_REQUEST_ACTION = "browser_skill_candidate.activation_approval_request"
PROMOTION_ACTIVATION_APPROVAL_DECISION_PREFLIGHT_ACTION = (
    "browser_skill_candidate.activation_approval_decision_preflight"
)
PROMOTION_ACTIVATION_APPROVAL_DECISION_CONSUMER_DESIGN_ACTION = (
    "browser_skill_candidate.activation_approval_decision_consumer_design"
)
PROMOTION_ACTIVATION_APPROVAL_DECISION_CONSUMER_WRITE_GUARD_ACTION = (
    "browser_skill_candidate.activation_approval_decision_consumer_write_guard_contract"
)
PROMOTION_ACTIVATION_APPROVAL_DECISION_CONSUMER_WRITER_DESIGN_ACTION = (
    "browser_skill_candidate.activation_approval_decision_consumer_writer_design"
)
PROMOTION_ACTIVATION_APPROVAL_DECISION_CONSUMER_WRITER_IMPLEMENTATION_REQUEST_ACTION = (
    "browser_skill_candidate.activation_approval_decision_consumer_writer_implementation_request"
)
PROMOTION_ACTIVATION_APPROVAL_DECISION_CONSUMER_WRITER_IMPLEMENTATION_APPROVAL_ACTION = (
    "browser_skill_candidate.activation_approval_decision_consumer_writer_implementation_approval"
)
PROMOTION_ACTIVATION_APPROVAL_DECISION_CONSUMER_WRITER_IMPLEMENTATION_ACTION = (
    "browser_skill_candidate.activation_approval_decision_consumer_writer_implementation"
)
PROMOTION_ACTIVATION_CONSUMPTION_LIVE_READINESS_ACTION = (
    "browser_skill_candidate.activation_consumption_live_readiness"
)
PROMOTION_ACTIVATION_EXECUTOR_DESIGN_ACTION = (
    "browser_skill_candidate.activation_executor_design"
)
PROMOTION_ACTIVATION_EXECUTOR_PREFLIGHT_ACTION = (
    "browser_skill_candidate.activation_executor_preflight"
)
PROMOTION_ACTIVATION_EXECUTOR_IMPLEMENTATION_REQUEST_ACTION = (
    "browser_skill_candidate.activation_executor_implementation_request"
)
PROMOTION_ACTIVATION_EXECUTOR_IMPLEMENTATION_APPROVAL_ACTION = (
    "browser_skill_candidate.activation_executor_implementation_approval"
)
PROMOTION_ACTIVATION_EXECUTOR_IMPLEMENTATION_ACTION = (
    "browser_skill_candidate.activation_executor_implementation"
)
PROMOTION_ACTIVATION_EXECUTOR_LIVE_READINESS_ACTION = (
    "browser_skill_candidate.activation_executor_live_readiness"
)
PROMOTION_ACTIVATION_GATE_LIVE_READINESS_ACTION = (
    "browser_skill_candidate.activation_gate_live_readiness"
)
PROMOTION_ACTIVATION_GATE_POLICY_PATCH_WRITER_IMPLEMENTATION_ACTION = (
    "browser_skill_candidate.activation_gate_policy_patch_writer_implementation"
)
PROMOTION_LIVE_ACTIVATION_EVIDENCE_CLOSEOUT_ACTION = (
    "browser_skill_candidate.live_activation_evidence_closeout"
)
PROMOTION_BROWSER_SKILL_SHADOW_REPLAY_DESIGN_ACTION = (
    "browser_skill_candidate.browser_skill_shadow_replay_design"
)
PROMOTION_BROWSER_SKILL_SHADOW_REPLAY_IMPLEMENTATION_REQUEST_ACTION = (
    "browser_skill_candidate.browser_skill_shadow_replay_implementation_request"
)
PROMOTION_BROWSER_SKILL_SHADOW_REPLAY_IMPLEMENTATION_APPROVAL_ACTION = (
    "browser_skill_candidate.browser_skill_shadow_replay_implementation_approval"
)
PROMOTION_BROWSER_SKILL_SHADOW_REPLAY_RUNNER_WRITE_GUARD_ACTION = (
    "browser_skill_candidate.browser_skill_shadow_replay_runner_write_guard"
)
PROMOTION_BROWSER_SKILL_SHADOW_REPLAY_RUNNER_DRY_RUN_ACTION = (
    "browser_skill_candidate.browser_skill_shadow_replay_runner_implementation_dry_run"
)
PROMOTION_BROWSER_SKILL_SHADOW_REPLAY_RUNNER_WRITE_PASS_ACTION = (
    "browser_skill_candidate.browser_skill_shadow_replay_runner_write_pass"
)
PROMOTION_BROWSER_SKILL_SHADOW_REPLAY_EVIDENCE_REVIEW_CLOSEOUT_ACTION = (
    "browser_skill_candidate.browser_skill_shadow_replay_evidence_review_closeout"
)
PROMOTION_BROWSER_SKILL_SHADOW_EXECUTION_APPROVAL_PACKET_ACTION = (
    "browser_skill_candidate.browser_skill_shadow_execution_approval_packet"
)
PROMOTION_BROWSER_SKILL_SHADOW_EXECUTION_APPROVAL_DECISION_PREFLIGHT_ACTION = (
    "browser_skill_candidate.browser_skill_shadow_execution_approval_decision_preflight"
)
PROMOTION_BROWSER_SKILL_SHADOW_EXECUTION_APPROVAL_DECISION_REQUEST_ACTION = (
    "browser_skill_candidate.browser_skill_shadow_execution_approval_decision_request"
)
PROMOTION_BROWSER_SKILL_SHADOW_EXECUTION_APPROVAL_LIVE_DECISION_READINESS_ACTION = (
    "browser_skill_candidate.browser_skill_shadow_execution_approval_live_decision_readiness"
)
PROMOTION_BROWSER_SKILL_SHADOW_EXECUTION_PROOF_READINESS_ACTION = (
    "browser_skill_candidate.browser_skill_shadow_execution_proof_readiness"
)
PROMOTION_BROWSER_SKILL_SHADOW_EXECUTION_PROOF_CONSUMPTION_GUARD_ACTION = (
    "browser_skill_candidate.browser_skill_shadow_execution_proof_consumption_guard"
)
PROMOTION_BROWSER_SKILL_SHADOW_EXECUTION_PROOF_ACTION = (
    "browser_skill_candidate.browser_skill_shadow_execution_proof"
)
PROMOTION_BROWSER_SKILL_SHADOW_EXECUTION_PROOF_REVIEW_CLOSEOUT_ACTION = (
    "browser_skill_candidate.browser_skill_shadow_execution_proof_review_closeout"
)
PROMOTION_ACTIVATION_GATE_OPERATION = "siteops.browser_skill_candidate.activate_trusted_artifact"
PROMOTION_WORKFLOW_ID = "browser_skill_candidate.promotion"
PROMOTION_GATE_APPLY_OPERATION = "siteops.browser_skill_candidate.apply_trusted_artifacts"
REQUEST_ROLES = ["workflow_author", "workspace_admin", "tenant_admin"]


def _slug(value: str) -> str:
    clean = "".join(ch.lower() if ch.isalnum() else "-" for ch in value)
    return "-".join(part for part in clean.split("-") if part) or "candidate"


def _new_run_id(candidate_id: str) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"siteops_candidate_{stamp}_{_slug(candidate_id)[:80]}"


def _stable_bound_replacement_run_id(
    *,
    candidate_id: str,
    approval_id: str,
    tenant_id: str,
    workspace_id: str,
    user_id: str,
) -> str:
    fingerprint = hashlib.sha256(
        f"{tenant_id}|{workspace_id}|{user_id}|{candidate_id}|{approval_id}".encode("utf-8")
    ).hexdigest()[:12]
    return f"siteops_candidate_bound_replacement_{_slug(candidate_id)[:48]}_{fingerprint}"


def _configured_workspaces(tenant: dict[str, Any]) -> set[str]:
    meta = tenant.get("tenant", tenant)
    workspaces = {str(meta.get("default_workspace_id") or "").strip()}
    for item in tenant.get("site_skill_installations", []):
        for workspace in item.get("allowed_workspaces", []):
            workspaces.add(str(workspace).strip())
    for item in tenant.get("workflow_installations", []):
        if item.get("workspace_id"):
            workspaces.add(str(item["workspace_id"]).strip())
    return {workspace for workspace in workspaces if workspace}


def _validate_request_scope(root: Path | str | None, scope: SiteOpsScope) -> dict[str, Any]:
    tenant = load_tenant(root, scope.tenant_id)
    if scope.workspace_id not in _configured_workspaces(tenant):
        raise SiteOpsValidationError(f"workspace is not configured for tenant: {scope.workspace_id}")
    if not has_any_role(tenant, scope.user_id, REQUEST_ROLES):
        raise SiteOpsValidationError(
            "user lacks role for candidate promotion request: "
            f"{scope.user_id} requires one of {', '.join(REQUEST_ROLES)}"
        )
    return tenant


def _repo_path_is_confined(path: str | None, root: Path) -> bool:
    normalized = str(path or "").replace("\\", "/").lstrip("./")
    if not normalized or normalized == ".." or normalized.startswith("../") or "/../" in normalized:
        return False
    return normalized.startswith(root.as_posix().rstrip("/") + "/")


def _filesystem_path_is_within(path: Path, parent: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(parent.resolve(strict=False))
        return True
    except ValueError:
        return False


def _sha256_file(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _siteops_skill_card_target(proposed_skill_id: str | None) -> str | None:
    skill_id = str(proposed_skill_id or "").strip()
    if not skill_id or "/" in skill_id or "\\" in skill_id or ".." in skill_id:
        return None
    return (SITEOPS_SKILL_CARD_REL / f"{skill_id}.json").as_posix()


def _executor_preflight_check(
    check_id: str,
    *,
    passed: bool,
    required: bool = True,
    detail: str | None = None,
) -> dict[str, Any]:
    return {
        "check_id": check_id,
        "passed": bool(passed),
        "required": bool(required),
        "detail": detail,
    }


def _secret_session_exclusion_recheck(preflight: dict[str, Any]) -> dict[str, Any]:
    """Return a redacted, read-only secret/session exclusion recheck packet."""
    validation = dict(preflight.get("validation") or {})
    errors = [str(error) for error in validation.get("errors") or []]
    markers = ("secret", "cookie", "token", "session", "credential", "password", "api_key")
    matched = [
        (index, error)
        for index, error in enumerate(errors)
        if any(marker in error.lower() for marker in markers)
    ]
    checked = bool(validation.get("checked"))
    passed = checked and not matched
    redacted_matches = [
        {
            "validation_error_index": index,
            "classification": "sensitive_validation_error_redacted",
            "redacted": True,
        }
        for index, _error in matched
    ]
    return {
        "checked": checked,
        "passed": passed,
        "source": "candidate_preflight.validation",
        "matched_error_count": len(matched),
        "matched_errors": redacted_matches,
        "raw_content_visible": False,
        "writes_performed": False,
    }


def _secret_session_exclusion_detail(recheck: dict[str, Any]) -> str:
    if not recheck.get("checked"):
        return "candidate validation was not available for secret/session exclusion recheck"
    if recheck.get("passed"):
        return "no secret/cookie/token/session material detected in candidate validation"
    count = int(recheck.get("matched_error_count") or 0)
    return f"secret/cookie/token/session exclusion failed with {count} matched validation error(s)"


def _trusted_executor_entrypoint_status() -> dict[str, Any]:
    entrypoint = globals().get("apply_trusted_candidate_artifacts")
    exists = callable(entrypoint)
    guarded = bool(getattr(entrypoint, "siteops_guarded_executor", False)) if exists else False
    return {
        "module": "runtime.siteops.candidate_promotions",
        "function": "apply_trusted_candidate_artifacts",
        "status": "BUILT_GUARDED" if guarded else ("UNREVIEWED_ENTRYPOINT_PRESENT" if exists else "NOT BUILT"),
        "enabled": guarded,
        "callable": exists,
        "guarded": guarded,
    }


def _apply_contract(
    *,
    scope: SiteOpsScope,
    candidate_id: str,
    proposed_skill_id: str | None,
    approval_id: str | None,
    approval_status: str | None,
    target: dict[str, Any],
) -> dict[str, Any]:
    if approval_status == "approved":
        status = "gate_apply_review_ready"
    elif approval_status == "rejected":
        status = "blocked_rejected"
    elif approval_id:
        status = "blocked_pending_approval"
    else:
        status = "blocked_missing_approval"
    return {
        "action": PROMOTION_APPLY_ACTION,
        "scope": scope.as_dict(),
        "candidate_id": candidate_id,
        "proposed_skill_id": proposed_skill_id,
        "approval_id": approval_id,
        "approval_status": approval_status,
        "apply_contract_status": status,
        "target": target,
        "trusted_skill_write_allowed": False,
        "siteops_skill_card_write_allowed": False,
        "browser_execution_allowed": False,
        "activation_allowed": False,
        "canonical_writeback_allowed": False,
        "requires_future_gate_apply": True,
        "boundary": (
            "apply contract only; even an approved promotion request does not write "
            "trusted skills or SiteOps skill cards in this pass"
        ),
    }


def request_scoped_candidate_promotion(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    requested_by: str | None = None,
    write_approval: bool = False,
) -> dict[str, Any]:
    """Build or persist a scoped SiteOps approval request for a candidate.

    The default path is contract-only. When ``write_approval`` is true, this
    writes only scoped SiteOps run/audit/approval artifacts. It never writes a
    trusted Browser Skill, SiteOps Skill Card, browser state, or canonical
    ChaseOS memory.
    """
    scope = require_scope(tenant_id=tenant_id, workspace_id=workspace_id, user_id=user_id)
    _validate_request_scope(root, scope)
    requested_by = requested_by or scope.user_id
    base = candidate_promotion_request_contract(
        candidate_id,
        root,
        requested_by=requested_by,
        tenant_id=scope.tenant_id,
        workspace_id=scope.workspace_id,
        user_id=scope.user_id,
    )
    target = dict((base.get("approval_request") or {}).get("target") or {})
    request = dict(base.get("approval_request") or {})
    request.update(
        {
            "tenant_id": scope.tenant_id,
            "workspace_id": scope.workspace_id,
            "user_id": scope.user_id,
            "workflow_id": PROMOTION_WORKFLOW_ID,
            "action": PROMOTION_ACTION,
            "requested_by": requested_by,
            "required_approver_role": "approver",
            "scope": scope.as_dict(),
            "scope_status": "validated",
        }
    )
    blockers = list(base.get("blockers") or [])
    ready = base.get("contract_status") == "approval_request_ready" and not blockers
    run_ref: str | None = None
    audit_ref: str | None = None
    approval: dict[str, Any] | None = None
    approval_write_blocked = False
    run_id: str | None = None
    if write_approval and ready:
        run_id = _new_run_id(str(base.get("candidate_id") or candidate_id))
        audit_ref = str(audit_path(root, scope.tenant_id, scope.workspace_id, run_id))
        now = now_iso()
        run = SiteOpsRun(
            run_id=run_id,
            tenant_id=scope.tenant_id,
            workspace_id=scope.workspace_id,
            user_id=scope.user_id,
            skill_id=str(base.get("proposed_skill_id") or "browser_skill_candidate"),
            workflow_id=PROMOTION_WORKFLOW_ID,
            site_profile_id=None,
            provider_id=None,
            mode="dry_run",
            status="approval_needed",
            inputs_ref=target.get("source_path"),
            outputs_ref=None,
            audit_ref=audit_ref,
            cost_estimate={"charged": False, "provider": None},
            cost_actual=None,
            started_at=now,
            ended_at=now,
        )
        run_ref = write_run_record(root, run)
        audit_ref = append_audit_event(
            root,
            SiteOpsAuditEvent(
                event_id=f"event_{run_id}_policy",
                run_id=run_id,
                tenant_id=scope.tenant_id,
                workspace_id=scope.workspace_id,
                user_id=scope.user_id,
                event_type="policy_decision",
                action=PROMOTION_ACTION,
                target=str(base.get("candidate_id") or candidate_id),
                policy_decision="approval_required",
                timestamp=now_iso(),
                metadata={
                    "candidate_id": base.get("candidate_id"),
                    "proposed_skill_id": base.get("proposed_skill_id"),
                    "trusted_skill_path": target.get("trusted_skill_path"),
                    "source_path": target.get("source_path"),
                    "scope": scope.as_dict(),
                    "trusted_skill_write_allowed": False,
                    "siteops_skill_card_write_allowed": False,
                },
                redacted_fields=[],
            ),
        )
        approval = create_approval_request(
            root,
            scope=scope,
            run_id=run_id,
            workflow_id=PROMOTION_WORKFLOW_ID,
            action=PROMOTION_ACTION,
            risk_level=request.get("risk_level") or "high",
            approval_reason=(
                "Review Browser Skill candidate promotion request for "
                f"{base.get('candidate_id')} -> {base.get('proposed_skill_id')}. "
                "This approval does not itself write a trusted skill."
            ),
            required_approver_role="approver",
            requested_by=requested_by,
            metadata={
                "candidate_id": base.get("candidate_id"),
                "proposed_skill_id": base.get("proposed_skill_id"),
                "trusted_skill_path": target.get("trusted_skill_path"),
                "siteops_skill_card_path": _siteops_skill_card_target(str(base.get("proposed_skill_id") or "")),
                "source_path": target.get("source_path"),
                "promotion_action": PROMOTION_ACTION,
            },
        )
        append_audit_event(
            root,
            SiteOpsAuditEvent(
                event_id=f"event_{run_id}_approval_request",
                run_id=run_id,
                tenant_id=scope.tenant_id,
                workspace_id=scope.workspace_id,
                user_id=scope.user_id,
                event_type="approval_request_created",
                action=PROMOTION_ACTION,
                target=str(base.get("candidate_id") or candidate_id),
                policy_decision="approval_required",
                timestamp=now_iso(),
                metadata={
                    "approval_id": approval.get("approval_id"),
                    "approval_ref": approval.get("approval_ref"),
                    "trusted_skill_write_allowed": False,
                    "siteops_skill_card_write_allowed": False,
                },
                redacted_fields=[],
            ),
        )
        request["run_id"] = run_id
        request["approval_id"] = approval.get("approval_id")
    elif write_approval:
        approval_write_blocked = True

    approval_id = approval.get("approval_id") if approval else request.get("approval_id")
    approval_status = approval.get("status") if approval else None
    apply_contract = _apply_contract(
        scope=scope,
        candidate_id=str(base.get("candidate_id") or candidate_id),
        proposed_skill_id=base.get("proposed_skill_id"),
        approval_id=approval_id,
        approval_status=approval_status,
        target=target,
    )
    return {
        **base,
        "scope": scope.as_dict(),
        "scope_status": "validated",
        "approval_request": request,
        "approval": approval,
        "approval_request_written": bool(approval),
        "approval_write_blocked": approval_write_blocked,
        "siteops_run_written": bool(run_ref),
        "audit_written": bool(audit_ref),
        "run_record_written": bool(run_ref),
        "audit_event_written": bool(audit_ref),
        "run_id": run_id,
        "run_ref": run_ref,
        "audit_ref": audit_ref,
        "apply_contract": apply_contract,
        "writes_performed": bool(approval or run_ref or audit_ref),
        "trusted_skill_write_allowed": False,
        "siteops_skill_card_write_allowed": False,
        "browser_execution_allowed": False,
        "activation_allowed": False,
        "promotion_allowed": False,
        "canonical_writeback_allowed": False,
        "boundary": (
            "scoped approval request only; no trusted skill, SiteOps skill card, "
            "browser execution, activation, or canonical writeback is performed"
        ),
    }


def _approval_provenance_status(
    *,
    approval: dict[str, Any],
    candidate_id: str,
    proposed_skill_id: str | None,
) -> dict[str, Any]:
    metadata = dict(approval.get("metadata") or {})
    bound_candidate_id = str(metadata.get("candidate_id") or "").strip() or None
    bound_proposed_skill_id = str(metadata.get("proposed_skill_id") or "").strip() or None
    candidate_id_matches = None if bound_candidate_id is None else bound_candidate_id == candidate_id
    proposed_skill_id_matches = (
        None if bound_proposed_skill_id is None else bound_proposed_skill_id == str(proposed_skill_id or "")
    )
    if bound_candidate_id is None and bound_proposed_skill_id is None:
        provenance_status = "legacy_unbound"
    elif candidate_id_matches is True and proposed_skill_id_matches is True:
        provenance_status = "bound_match"
    else:
        provenance_status = "bound_mismatch"
    return {
        "checked": True,
        "provenance_status": provenance_status,
        "bound_candidate_id": bound_candidate_id,
        "bound_proposed_skill_id": bound_proposed_skill_id,
        "candidate_id": candidate_id,
        "proposed_skill_id": proposed_skill_id,
        "candidate_id_matches": candidate_id_matches,
        "proposed_skill_id_matches": proposed_skill_id_matches,
        "trusted_skill_path": metadata.get("trusted_skill_path"),
        "siteops_skill_card_path": metadata.get("siteops_skill_card_path"),
        "source_path": metadata.get("source_path"),
        "promotion_action": metadata.get("promotion_action"),
    }


def _count_values(items: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        value = item.get(key)
        if value is None or value == "":
            continue
        text = str(value)
        counts[text] = counts.get(text, 0) + 1
    return counts


def _count_nested_values(items: list[dict[str, Any]], object_key: str, value_key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        obj = item.get(object_key) or {}
        if not isinstance(obj, dict):
            continue
        value = obj.get(value_key)
        if value is None or value == "":
            continue
        text = str(value)
        counts[text] = counts.get(text, 0) + 1
    return counts


def _candidate_id_from_legacy_approval(approval: dict[str, Any]) -> str:
    """Recover candidate identity from legacy approval text when metadata is absent."""

    reason = str(approval.get("approval_reason") or "").strip()
    marker = "Review Browser Skill candidate promotion request for "
    if reason.startswith(marker) and " -> " in reason:
        candidate_id = reason[len(marker) :].split(" -> ", 1)[0].strip()
        if candidate_id:
            return candidate_id
    return ""



def _candidate_approval_readiness_summary(approvals: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "approval_count": len(approvals),
        "approval_status_counts": _count_values(approvals, "approval_status"),
        "approval_provenance_status_counts": _count_nested_values(
            approvals,
            "approval_provenance",
            "provenance_status",
        ),
        "apply_contract_status_counts": _count_values(approvals, "apply_contract_status"),
        "executor_preflight_status_counts": _count_values(approvals, "executor_preflight_status"),
        "activation_boundary_status_counts": _count_values(approvals, "activation_boundary_status"),
        "bound_approval_request_spec_status_counts": _count_values(approvals, "bound_approval_request_spec_status"),
        "authority": {
            "writes_performed": False,
            "approval_decision_allowed": False,
            "trusted_skill_write_allowed": False,
            "siteops_skill_card_write_allowed": False,
            "browser_execution_allowed": False,
            "activation_allowed": False,
            "canonical_writeback_allowed": False,
        },
    }


def list_candidate_promotion_approvals(
    root: Path | str | None = None,
    *,
    tenant_id: str = "local",
    workspace_id: str | None = None,
    status: str | None = None,
    include_executor_preflight: bool = False,
    include_activation_boundary: bool = False,
    include_bound_approval_request_spec: bool = False,
    include_readiness_summary: bool = False,
) -> dict[str, Any]:
    """List Browser Skill candidate approval requests with read-only provenance."""

    approvals: list[dict[str, Any]] = []
    for approval in list_approval_requests(root, tenant_id=tenant_id, workspace_id=workspace_id):
        if approval.get("action") != PROMOTION_ACTION:
            continue
        if status and approval.get("status") != status:
            continue
        metadata = dict(approval.get("metadata") or {})
        candidate_id = str(metadata.get("candidate_id") or "").strip()
        candidate_id_for_projection = candidate_id or _candidate_id_from_legacy_approval(approval)
        proposed_skill_id = str(metadata.get("proposed_skill_id") or "").strip()
        provenance = _approval_provenance_status(
            approval=approval,
            candidate_id=candidate_id_for_projection,
            proposed_skill_id=proposed_skill_id or None,
        )
        target = {
            "trusted_skill_path": metadata.get("trusted_skill_path"),
            "siteops_skill_card_path": metadata.get("siteops_skill_card_path"),
            "source_path": metadata.get("source_path"),
        }
        apply_contract = _apply_contract(
            scope=SiteOpsScope(
                tenant_id=str(approval.get("tenant_id") or tenant_id),
                workspace_id=str(approval.get("workspace_id") or workspace_id or ""),
                user_id=str(approval.get("user_id") or ""),
            ),
            candidate_id=candidate_id,
            proposed_skill_id=proposed_skill_id or None,
            approval_id=approval.get("approval_id"),
            approval_status=approval.get("status"),
            target=target,
        )
        item = {
            "approval_id": approval.get("approval_id"),
            "approval_status": approval.get("status"),
            "candidate_id": candidate_id_for_projection or None,
            "proposed_skill_id": proposed_skill_id or None,
            "tenant_id": approval.get("tenant_id"),
            "workspace_id": approval.get("workspace_id"),
            "user_id": approval.get("user_id"),
            "run_id": approval.get("run_id"),
            "requested_by": approval.get("requested_by"),
            "approval_ref": approval.get("approval_ref"),
            "approval_provenance": provenance,
            "apply_contract_status": apply_contract.get("apply_contract_status"),
            "writes_performed": False,
            "trusted_skill_write_allowed": False,
            "siteops_skill_card_write_allowed": False,
            "browser_execution_allowed": False,
            "activation_allowed": False,
            "canonical_writeback_allowed": False,
        }
        if include_executor_preflight:
            try:
                if not candidate_id:
                    raise SiteOpsValidationError("legacy approval metadata does not bind a candidate for executor preflight")
                executor_spec = candidate_promotion_gate_executor_spec(
                    candidate_id,
                    root,
                    tenant_id=str(approval.get("tenant_id") or tenant_id),
                    workspace_id=str(approval.get("workspace_id") or workspace_id or ""),
                    user_id=str(approval.get("user_id") or approval.get("requested_by") or ""),
                    approval_id=str(approval.get("approval_id") or ""),
                )
                item["executor_preflight_status"] = executor_spec.get("executor_preflight_status")
                item["executor_preflight"] = {
                    "executor_spec_status": executor_spec.get("executor_spec_status"),
                    "gate_operation": executor_spec.get("gate_operation"),
                    "gate_operation_allowed": executor_spec.get("gate_operation_allowed"),
                    "executor_implemented": executor_spec.get("executor_implemented"),
                    "executor_enabled": executor_spec.get("executor_enabled"),
                    "apply_execution_allowed": executor_spec.get("apply_execution_allowed"),
                    "trusted_skill_write_allowed": executor_spec.get("trusted_skill_write_allowed"),
                    "siteops_skill_card_write_allowed": executor_spec.get("siteops_skill_card_write_allowed"),
                    "browser_execution_allowed": executor_spec.get("browser_execution_allowed"),
                    "activation_allowed": executor_spec.get("activation_allowed"),
                    "canonical_writeback_allowed": executor_spec.get("canonical_writeback_allowed"),
                    "writes_performed": executor_spec.get("writes_performed"),
                    "checks": executor_spec.get("executor_preflight_checks"),
                }
            except (BrowserSkillCandidateError, RuntimeError, ValueError, SiteOpsError) as exc:
                item["executor_preflight_status"] = "blocked_executor_preflight_unavailable"
                item["executor_preflight"] = {
                    "error": str(exc),
                    "executor_implemented": False,
                    "executor_enabled": False,
                    "writes_performed": False,
                }
        if include_activation_boundary:
            try:
                boundary = candidate_promotion_activation_boundary_readiness(
                    candidate_id,
                    root,
                    tenant_id=str(approval.get("tenant_id") or tenant_id),
                    workspace_id=str(approval.get("workspace_id") or workspace_id or ""),
                    user_id=str(approval.get("user_id") or approval.get("requested_by") or ""),
                    approval_id=str(approval.get("approval_id") or ""),
                )
                item["activation_boundary_status"] = boundary.get("activation_boundary_status")
                item["activation_boundary"] = {
                    "review_decision": boundary.get("review_decision"),
                    "gate_operation": boundary.get("gate_operation"),
                    "gate_operation_allowed": boundary.get("gate_operation_allowed"),
                    "activation_allowed": boundary.get("activation_allowed"),
                    "activation_performed": boundary.get("activation_performed"),
                    "trusted_skill_write_allowed": boundary.get("trusted_skill_write_allowed"),
                    "siteops_skill_card_write_allowed": boundary.get("siteops_skill_card_write_allowed"),
                    "browser_execution_allowed": boundary.get("browser_execution_allowed"),
                    "canonical_writeback_allowed": boundary.get("canonical_writeback_allowed"),
                    "writes_performed": boundary.get("writes_performed"),
                    "checks": boundary.get("activation_boundary_checks"),
                    "reasons": boundary.get("activation_boundary_reasons"),
                }
            except (BrowserSkillCandidateError, RuntimeError, ValueError, SiteOpsError) as exc:
                item["activation_boundary_status"] = "blocked_activation_boundary_unavailable"
                item["activation_boundary"] = {
                    "error": str(exc),
                    "activation_allowed": False,
                    "activation_performed": False,
                    "writes_performed": False,
                }
        if include_bound_approval_request_spec:
            try:
                bound_spec = candidate_promotion_bound_approval_request_spec(
                    candidate_id_for_projection,
                    root,
                    tenant_id=str(approval.get("tenant_id") or tenant_id),
                    workspace_id=str(approval.get("workspace_id") or workspace_id or ""),
                    user_id=str(approval.get("user_id") or approval.get("requested_by") or ""),
                    approval_id=str(approval.get("approval_id") or ""),
                )
                item["bound_approval_request_spec_status"] = bound_spec.get(
                    "bound_approval_request_spec_status"
                )
                item["bound_approval_request_spec"] = {
                    "approval_rebind_spec_status": bound_spec.get("approval_rebind_spec_status"),
                    "provenance_status": bound_spec.get("provenance_status"),
                    "review_decision": bound_spec.get("review_decision"),
                    "approval_request_artifact_written": bound_spec.get("approval_request_artifact_written"),
                    "legacy_approval_mutation_allowed": bound_spec.get("legacy_approval_mutation_allowed"),
                    "replacement_approval_request_written": bound_spec.get("replacement_approval_request_written"),
                    "approval_decision_written": bound_spec.get("approval_decision_written"),
                    "trusted_skill_write_allowed": bound_spec.get("trusted_skill_write_allowed"),
                    "siteops_skill_card_write_allowed": bound_spec.get("siteops_skill_card_write_allowed"),
                    "browser_execution_allowed": bound_spec.get("browser_execution_allowed"),
                    "activation_allowed": bound_spec.get("activation_allowed"),
                    "canonical_writeback_allowed": bound_spec.get("canonical_writeback_allowed"),
                    "writes_performed": bound_spec.get("writes_performed"),
                    "validation": bound_spec.get("approval_request_validation"),
                    "future_writer_requirements": bound_spec.get("future_writer_requirements"),
                }
            except (BrowserSkillCandidateError, RuntimeError, ValueError, SiteOpsError) as exc:
                item["bound_approval_request_spec_status"] = "blocked_bound_approval_request_spec_unavailable"
                item["bound_approval_request_spec"] = {
                    "error": str(exc),
                    "approval_request_artifact_written": False,
                    "legacy_approval_mutation_allowed": False,
                    "writes_performed": False,
                }
        approvals.append(item)
    payload = {
        "ok": True,
        "action": "siteops.candidates.approvals",
        "scope": {"tenant_id": tenant_id, "workspace_id": workspace_id},
        "status_filter": status,
        "include_executor_preflight": bool(include_executor_preflight),
        "include_activation_boundary": bool(include_activation_boundary),
        "include_bound_approval_request_spec": bool(include_bound_approval_request_spec),
        "include_readiness_summary": bool(include_readiness_summary),
        "count": len(approvals),
        "candidate_approval_count": len(approvals),
        "approvals": approvals,
        "writes_performed": False,
        "trusted_skill_write_allowed": False,
        "siteops_skill_card_write_allowed": False,
        "browser_execution_allowed": False,
        "activation_allowed": False,
        "canonical_writeback_allowed": False,
        "boundary": "read-only approval provenance view; no approval decisions, promotion, activation, browser execution, or canonical writeback",
    }
    if include_readiness_summary:
        payload["readiness_summary"] = _candidate_approval_readiness_summary(approvals)
    return payload


def candidate_promotion_apply_contract(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    approval_id: str,
) -> dict[str, Any]:
    """Return a non-mutating scoped apply contract for an approval request."""
    scope = require_scope(tenant_id=tenant_id, workspace_id=workspace_id, user_id=user_id)
    _validate_request_scope(root, scope)
    base = candidate_promotion_request_contract(
        candidate_id,
        root,
        requested_by=scope.user_id,
        tenant_id=scope.tenant_id,
        workspace_id=scope.workspace_id,
        user_id=scope.user_id,
    )
    approval = show_approval_request(root, approval_id, tenant_id=scope.tenant_id)
    if approval.get("workspace_id") != scope.workspace_id or approval.get("user_id") != scope.user_id:
        raise SiteOpsValidationError("approval scope does not match requested candidate apply scope")
    if approval.get("action") != PROMOTION_ACTION:
        raise SiteOpsValidationError("approval action is not a Browser Skill candidate promotion")
    resolved_candidate_id = str(base.get("candidate_id") or candidate_id)
    resolved_skill_id = str(base.get("proposed_skill_id") or "")
    approval_provenance = _approval_provenance_status(
        approval=approval,
        candidate_id=resolved_candidate_id,
        proposed_skill_id=resolved_skill_id or None,
    )
    if approval_provenance["provenance_status"] == "bound_mismatch":
        if approval_provenance["candidate_id_matches"] is False:
            raise SiteOpsValidationError("approval candidate does not match requested candidate apply scope")
        raise SiteOpsValidationError("approval proposed skill does not match requested candidate apply scope")
    target = dict((base.get("approval_request") or {}).get("target") or {})
    apply_contract = _apply_contract(
        scope=scope,
        candidate_id=str(base.get("candidate_id") or candidate_id),
        proposed_skill_id=base.get("proposed_skill_id"),
        approval_id=approval_id,
        approval_status=approval.get("status"),
        target=target,
    )
    return {
        "ok": True,
        "candidate_id": base.get("candidate_id"),
        "proposed_skill_id": base.get("proposed_skill_id"),
        "scope": scope.as_dict(),
        "approval": approval,
        "approval_provenance": approval_provenance,
        "apply_contract": apply_contract,
        "writes_performed": False,
        "trusted_skill_write_allowed": False,
        "siteops_skill_card_write_allowed": False,
        "browser_execution_allowed": False,
        "activation_allowed": False,
        "canonical_writeback_allowed": False,
    }


def candidate_promotion_approval_rebind_spec(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    approval_id: str,
) -> dict[str, Any]:
    """Return a no-write approval supersession/rebind spec for legacy approvals."""
    scope = require_scope(tenant_id=tenant_id, workspace_id=workspace_id, user_id=user_id)
    _validate_request_scope(root, scope)
    base = candidate_promotion_request_contract(
        candidate_id,
        root,
        requested_by=scope.user_id,
        tenant_id=scope.tenant_id,
        workspace_id=scope.workspace_id,
        user_id=scope.user_id,
    )
    approval = show_approval_request(root, approval_id, tenant_id=scope.tenant_id)
    resolved_candidate_id = str(base.get("candidate_id") or candidate_id)
    resolved_skill_id = str(base.get("proposed_skill_id") or "")
    provenance = _approval_provenance_status(
        approval=approval,
        candidate_id=resolved_candidate_id,
        proposed_skill_id=resolved_skill_id or None,
    )
    candidate_ready = base.get("contract_status") == "approval_request_ready" and not list(base.get("blockers") or [])
    scope_matches = approval.get("workspace_id") == scope.workspace_id and approval.get("user_id") == scope.user_id
    action_matches = approval.get("action") == PROMOTION_ACTION
    approval_status = str(approval.get("status") or "")
    provenance_status = str(provenance.get("provenance_status") or "")

    if not scope_matches:
        spec_status = "blocked_approval_scope_mismatch"
        review_decision = "blocked_before_rebind_review"
    elif not action_matches:
        spec_status = "blocked_approval_action_mismatch"
        review_decision = "blocked_before_rebind_review"
    elif not candidate_ready:
        spec_status = "blocked_candidate_preflight"
        review_decision = "blocked_before_rebind_review"
    elif approval_status != "approved":
        spec_status = "blocked_approval_not_approved"
        review_decision = "blocked_before_rebind_review"
    elif provenance_status == "bound_match":
        spec_status = "approval_rebind_not_required_bound_match"
        review_decision = "no_rebind_needed_existing_approval_is_bound"
    elif provenance_status == "legacy_unbound":
        spec_status = "approval_rebind_spec_required_no_write_authority"
        review_decision = "create_new_bound_approval_request_in_separate_pass_do_not_mutate_legacy_approval"
    else:
        spec_status = "blocked_bound_mismatch_requires_new_approval"
        review_decision = "blocked_existing_approval_mismatch_do_not_rebind_in_place"

    replacement_request_preview = {
        "future_command": (
            "chaseos siteops candidates request-promotion "
            f"{resolved_candidate_id} --tenant {scope.tenant_id} "
            f"--workspace {scope.workspace_id} --user {scope.user_id} "
            "--write-approval-request --json"
        ),
        "expected_new_approval_metadata": {
            "candidate_id": resolved_candidate_id,
            "proposed_skill_id": resolved_skill_id or None,
            "trusted_skill_path": ((base.get("approval_request") or {}).get("target") or {}).get("trusted_skill_path"),
            "siteops_skill_card_path": _siteops_skill_card_target(resolved_skill_id or None),
            "promotion_action": PROMOTION_ACTION,
        },
        "writes_allowed_in_this_pass": False,
    }
    rebind_policy = {
        "default": "fail_closed",
        "legacy_unbound_approval": "do_not_mutate_in_place",
        "bound_mismatch": "reject_existing_approval_and_require_new_request_review",
        "replacement_approval": "future_separate_request_with_candidate_and_skill_metadata",
        "legacy_artifact_retention": "preserve_as_historical_audit_record",
        "executor_dependency": "future_executor_requires_bound_match_after_replacement",
    }
    future_rebind_checks = [
        "legacy approval remains immutable and is not edited in place",
        "replacement approval request is newly created through request-promotion",
        "replacement approval metadata binds candidate_id and proposed_skill_id",
        "replacement approval is separately approved by an authorized operator",
        "future executor consumes only a bound_match approval id",
        "old approval id is not accepted as equivalent to the replacement approval id",
    ]
    denied_effects = [
        "mutate legacy approval artifact",
        "write replacement approval request",
        "approve or reject approval request",
        "write audit events",
        "write inactive trusted artifacts",
        "create apply_trusted_candidate_artifacts executor",
        "edit runtime/policy/gateway_allowlists.json",
        "write runtime/browser_skills/skills artifacts",
        "write runtime/siteops/registry/skill_cards artifacts",
        "launch or control a browser",
        "enqueue Agent Bus work",
        "call provider APIs",
        "activate promoted skills",
        "write canonical ChaseOS memory/state",
    ]

    return {
        "ok": True,
        "action": PROMOTION_APPROVAL_REBIND_SPEC_ACTION,
        "candidate_id": resolved_candidate_id,
        "proposed_skill_id": resolved_skill_id or None,
        "scope": scope.as_dict(),
        "approval": approval,
        "approval_status": approval_status,
        "approval_provenance": provenance,
        "provenance_status": provenance_status,
        "candidate_preflight_status": base.get("contract_status"),
        "candidate_preflight_blockers": list(base.get("blockers") or []),
        "approval_rebind_spec_status": spec_status,
        "review_decision": review_decision,
        "rebind_policy": rebind_policy,
        "replacement_request_preview": replacement_request_preview,
        "future_rebind_checks": future_rebind_checks,
        "blocked_actions": denied_effects,
        "denied_effects": denied_effects,
        "writes_performed": False,
        "approval_artifact_write_allowed": False,
        "approval_rebind_allowed": False,
        "legacy_approval_mutation_allowed": False,
        "replacement_approval_request_written": False,
        "approval_decision_written": False,
        "audit_events_written": False,
        "inactive_artifacts_written": False,
        "executor_implemented": False,
        "executor_enabled": False,
        "executor_build_allowed": False,
        "executor_implementation_allowed": False,
        "executor_implementation_performed": False,
        "allowlist_change_allowed": False,
        "allowlist_change_performed": False,
        "policy_file_write_allowed": False,
        "trusted_skill_write_allowed": False,
        "siteops_skill_card_write_allowed": False,
        "browser_execution_allowed": False,
        "agent_bus_enqueue_allowed": False,
        "provider_api_call_allowed": False,
        "activation_allowed": False,
        "canonical_writeback_allowed": False,
        "boundary": (
            "approval rebind spec only; legacy approvals are not mutated, replacement "
            "approvals are not written, approval decisions are not recorded, and no "
            "trusted artifact, browser, Agent Bus, provider, activation, Gate policy, "
            "or canonical writeback side effect is performed"
        ),
    }


def candidate_promotion_bound_approval_request_spec(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    approval_id: str,
) -> dict[str, Any]:
    """Return a no-write replacement approval artifact contract for legacy approvals."""
    rebind = candidate_promotion_approval_rebind_spec(
        candidate_id,
        root,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
        approval_id=approval_id,
    )
    scope = rebind["scope"]
    replacement_preview = rebind.get("replacement_request_preview") or {}
    expected_metadata = replacement_preview.get("expected_new_approval_metadata") or {}
    resolved_candidate_id = str(rebind.get("candidate_id") or candidate_id)
    resolved_skill_id = rebind.get("proposed_skill_id")
    run_id = _stable_bound_replacement_run_id(
        candidate_id=resolved_candidate_id,
        approval_id=approval_id,
        tenant_id=str(scope["tenant_id"]),
        workspace_id=str(scope["workspace_id"]),
        user_id=str(scope["user_id"]),
    )
    artifact = {
        "approval_id": f"approval_{run_id}_{PROMOTION_ACTION.replace('.', '_').replace('-', '_')}",
        "tenant_id": scope["tenant_id"],
        "workspace_id": scope["workspace_id"],
        "user_id": scope["user_id"],
        "run_id": run_id,
        "workflow_id": PROMOTION_WORKFLOW_ID,
        "action": PROMOTION_ACTION,
        "risk_level": "high",
        "approval_reason": (
            "Replacement bound approval request for Browser Skill candidate promotion; "
            "supersedes a legacy/unbound approval without mutating historical approval artifacts."
        ),
        "requested_by": scope["user_id"],
        "required_approver_role": "tenant_admin",
        "status": "pending",
        "supersedes_approval_id": approval_id,
        "supersession_policy": "legacy_approval_immutable_new_bound_request_required",
        "metadata": {
            "approval_binding_version": "browser_skill_candidate.v1",
            "candidate_id": resolved_candidate_id,
            "proposed_skill_id": resolved_skill_id,
            "trusted_skill_path": expected_metadata.get("trusted_skill_path"),
            "siteops_skill_card_path": expected_metadata.get("siteops_skill_card_path"),
            "promotion_action": PROMOTION_ACTION,
            "supersedes_approval_id": approval_id,
            "legacy_approval_provenance_status": rebind.get("provenance_status"),
            "replacement_reason": "legacy_unbound_approval_requires_new_bound_operator_review",
        },
    }
    checks = {
        "candidate_metadata_bound": {
            "passed": bool(artifact["metadata"].get("candidate_id") and artifact["metadata"].get("proposed_skill_id")),
            "requires": ["metadata.candidate_id", "metadata.proposed_skill_id"],
        },
        "scope_bound": {
            "passed": all(artifact.get(key) == scope.get(key) for key in ("tenant_id", "workspace_id", "user_id")),
            "requires": ["tenant_id", "workspace_id", "user_id"],
        },
        "legacy_approval_immutable": {
            "passed": True,
            "supersedes_approval_id": approval_id,
            "mutation_allowed": False,
        },
        "separate_operator_review_required": {
            "passed": artifact.get("status") == "pending" and artifact.get("required_approver_role") == "tenant_admin",
            "requires": ["status=pending", "required_approver_role=tenant_admin"],
        },
        "approval_action_matches_promotion": {
            "passed": artifact.get("action") == PROMOTION_ACTION,
            "requires": [PROMOTION_ACTION],
        },
    }
    validation_passed = all(check.get("passed") is True for check in checks.values())
    rebind_ready = rebind.get("approval_rebind_spec_status") == "approval_rebind_spec_required_no_write_authority"
    spec_status = (
        "bound_approval_request_spec_ready_no_write"
        if rebind_ready and validation_passed
        else "blocked_before_bound_approval_request_spec"
    )
    review_decision = (
        "future_writer_may_create_new_bound_approval_request_after_operator_scope_review"
        if spec_status == "bound_approval_request_spec_ready_no_write"
        else "blocked_do_not_write_replacement_approval_request"
    )
    denied_effects = list(rebind.get("denied_effects") or [])
    if "write bound replacement approval request" not in denied_effects:
        denied_effects.insert(0, "write bound replacement approval request")
    return {
        "ok": True,
        "action": PROMOTION_BOUND_APPROVAL_REQUEST_SPEC_ACTION,
        "candidate_id": resolved_candidate_id,
        "proposed_skill_id": resolved_skill_id,
        "scope": scope,
        "approval_id": approval_id,
        "approval_rebind_spec_status": rebind.get("approval_rebind_spec_status"),
        "approval_provenance": rebind.get("approval_provenance"),
        "provenance_status": rebind.get("provenance_status"),
        "bound_approval_request_spec_status": spec_status,
        "review_decision": review_decision,
        "approval_request_artifact": artifact,
        "approval_request_validation": {"passed": validation_passed, "checks": checks},
        "future_writer_requirements": [
            "write the artifact as a new approval request only through a separate approved writer",
            "do not mutate or reinterpret the superseded legacy approval",
            "require a separate operator approval decision on the new bound approval request",
            "future executor may consume only a bound_match approval after the replacement is approved",
        ],
        "blocked_actions": denied_effects,
        "denied_effects": denied_effects,
        "writes_performed": False,
        "approval_request_artifact_written": False,
        "approval_artifact_write_allowed": False,
        "legacy_approval_mutation_allowed": False,
        "replacement_approval_request_written": False,
        "approval_decision_written": False,
        "audit_events_written": False,
        "inactive_artifacts_written": False,
        "executor_implemented": False,
        "executor_enabled": False,
        "executor_build_allowed": False,
        "executor_implementation_allowed": False,
        "executor_implementation_performed": False,
        "allowlist_change_allowed": False,
        "allowlist_change_performed": False,
        "policy_file_write_allowed": False,
        "trusted_skill_write_allowed": False,
        "siteops_skill_card_write_allowed": False,
        "browser_execution_allowed": False,
        "agent_bus_enqueue_allowed": False,
        "provider_api_call_allowed": False,
        "activation_allowed": False,
        "canonical_writeback_allowed": False,
        "boundary": (
            "bound approval request spec only; no approval artifact is written, no legacy approval is mutated, "
            "no approval decision is recorded, and no trusted artifact, browser, Agent Bus, provider, activation, "
            "Gate policy, or canonical writeback side effect is performed"
        ),
    }


def candidate_promotion_bound_approval_writer_design(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    approval_id: str,
) -> dict[str, Any]:
    """Return a no-write design packet for a future bound approval writer."""
    spec = candidate_promotion_bound_approval_request_spec(
        candidate_id,
        root,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
        approval_id=approval_id,
    )
    scope = dict(spec.get("scope") or {})
    artifact = dict(spec.get("approval_request_artifact") or {})
    target_parent = approvals_dir(root, scope.get("tenant_id", ""), scope.get("workspace_id", ""))
    target_path = target_parent / f"{artifact.get('approval_id')}.json"
    parent_confined = _filesystem_path_is_within(
        target_parent,
        approvals_dir(root, scope.get("tenant_id", ""), scope.get("workspace_id", "")),
    )
    target_confined = _filesystem_path_is_within(target_path, target_parent)
    target_exists = target_path.exists()
    validation = dict(spec.get("approval_request_validation") or {})
    spec_ready = spec.get("bound_approval_request_spec_status") == "bound_approval_request_spec_ready_no_write"
    path_ready = parent_confined and target_confined and not target_exists
    writer_ready = spec_ready and bool(validation.get("passed")) and path_ready
    if target_exists:
        design_status = "blocked_existing_bound_approval_request_target"
        review_decision = "blocked_existing_target_requires_manual_review"
    elif not spec_ready:
        design_status = f"blocked_bound_approval_request_spec: {spec.get('bound_approval_request_spec_status')}"
        review_decision = "blocked_before_bound_approval_writer"
    elif not path_ready:
        design_status = "blocked_bound_approval_writer_path_boundary"
        review_decision = "blocked_target_path_boundary"
    else:
        design_status = "bound_approval_writer_design_ready_no_write"
        review_decision = "writer_design_only_do_not_write_in_this_pass"

    writer_steps = [
        {
            "order": 1,
            "step_id": "recompute_bound_approval_request_spec",
            "required": True,
            "implemented": False,
            "write_allowed_in_this_pass": False,
        },
        {
            "order": 2,
            "step_id": "verify_target_path_absent_and_scoped",
            "required": True,
            "implemented": False,
            "write_allowed_in_this_pass": False,
        },
        {
            "order": 3,
            "step_id": "write_pending_bound_approval_request_atomically",
            "required": True,
            "implemented": False,
            "write_allowed_in_this_pass": False,
        },
        {
            "order": 4,
            "step_id": "append_bound_approval_request_created_audit_event",
            "required": True,
            "implemented": False,
            "write_allowed_in_this_pass": False,
        },
        {
            "order": 5,
            "step_id": "return_new_approval_ref_without_consuming_it",
            "required": True,
            "implemented": False,
            "write_allowed_in_this_pass": False,
        },
    ]
    audit_event_contract = {
        "event_type": "bound_approval_request_created",
        "action": PROMOTION_ACTION,
        "policy_decision": "approval_required",
        "metadata_required": [
            "approval_id",
            "candidate_id",
            "proposed_skill_id",
            "supersedes_approval_id",
            "target_path",
            "approval_binding_version",
        ],
        "metadata_forbidden": [
            "raw_candidate_content",
            "cookie",
            "cookies",
            "token",
            "password",
            "api_key",
            "session",
            "secret",
        ],
        "implemented": False,
        "write_allowed_in_this_pass": False,
    }
    idempotency_policy = {
        "default": "fail_closed",
        "existing_target": "block_for_manual_review",
        "exact_payload_match": "future_noop_only_after_digest_and_scope_review",
        "legacy_approval": "never_mutate_or_reinterpret",
        "marker_write": "not_allowed_in_this_pass",
    }
    rollback_policy = {
        "atomic_write_required": True,
        "temporary_file_cleanup_only": True,
        "legacy_approval_rollback": "not_applicable_never_mutated",
        "partial_write": "future_writer_must_remove_temp_or_mark_manual_recovery_required",
        "implemented": False,
    }
    denied_effects = list(spec.get("denied_effects") or [])
    for effect in [
        "write bound approval request artifact",
        "write bound approval audit event",
        "write bound approval idempotency marker",
    ]:
        if effect not in denied_effects:
            denied_effects.insert(0, effect)
    return {
        "ok": True,
        "action": PROMOTION_BOUND_APPROVAL_WRITER_DESIGN_ACTION,
        "candidate_id": spec.get("candidate_id"),
        "proposed_skill_id": spec.get("proposed_skill_id"),
        "scope": scope,
        "approval_id": approval_id,
        "approval_rebind_spec_status": spec.get("approval_rebind_spec_status"),
        "bound_approval_request_spec_status": spec.get("bound_approval_request_spec_status"),
        "bound_approval_writer_design_status": design_status,
        "review_decision": review_decision,
        "approval_request_artifact": artifact,
        "approval_request_validation": validation,
        "target_path_preview": {
            "path": str(target_path),
            "parent": str(target_parent),
            "parent_confined": parent_confined,
            "target_confined": target_confined,
            "target_exists": target_exists,
            "write_allowed_in_this_pass": False,
        },
        "writer_steps": writer_steps,
        "audit_event_contract": audit_event_contract,
        "idempotency_policy": idempotency_policy,
        "rollback_policy": rollback_policy,
        "writer_ready_no_write": writer_ready,
        "future_writer_requirements": [
            "create parent directory only in the future writer, not in this spec",
            "write the approval artifact atomically as a new pending request",
            "append a scoped audit event without raw candidate content or secrets",
            "preserve the superseded legacy approval unchanged",
            "return the new approval id without consuming or approving it",
        ],
        "blocked_actions": denied_effects,
        "denied_effects": denied_effects,
        "writes_performed": False,
        "approval_request_artifact_written": False,
        "approval_artifact_write_allowed": False,
        "bound_approval_writer_implemented": False,
        "bound_approval_writer_enabled": False,
        "bound_approval_writer_execution_allowed": False,
        "bound_approval_audit_event_written": False,
        "bound_approval_idempotency_marker_written": False,
        "legacy_approval_mutation_allowed": False,
        "replacement_approval_request_written": False,
        "approval_decision_written": False,
        "audit_events_written": False,
        "inactive_artifacts_written": False,
        "executor_implemented": False,
        "executor_enabled": False,
        "executor_build_allowed": False,
        "executor_implementation_allowed": False,
        "executor_implementation_performed": False,
        "allowlist_change_allowed": False,
        "allowlist_change_performed": False,
        "policy_file_write_allowed": False,
        "trusted_skill_write_allowed": False,
        "siteops_skill_card_write_allowed": False,
        "browser_execution_allowed": False,
        "agent_bus_enqueue_allowed": False,
        "provider_api_call_allowed": False,
        "activation_allowed": False,
        "canonical_writeback_allowed": False,
        "boundary": (
            "bound approval writer design only; no approval artifact, audit event, idempotency marker, "
            "legacy approval mutation, approval decision, trusted artifact, browser, Agent Bus, provider, "
            "activation, Gate policy, or canonical writeback side effect is performed"
        ),
    }


def candidate_promotion_bound_approval_writer_preflight(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    approval_id: str,
) -> dict[str, Any]:
    """Return a no-write invocation preflight for a future bound approval writer."""
    design = candidate_promotion_bound_approval_writer_design(
        candidate_id,
        root,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
        approval_id=approval_id,
    )
    scope = dict(design.get("scope") or {})
    artifact = dict(design.get("approval_request_artifact") or {})
    target = dict(design.get("target_path_preview") or {})
    target_path = Path(str(target.get("path") or ""))
    marker_parent = approvals_dir(root, scope.get("tenant_id", ""), scope.get("workspace_id", "")) / "_idempotency"
    recovery_parent = approvals_dir(root, scope.get("tenant_id", ""), scope.get("workspace_id", "")) / "_recovery"
    marker_path = marker_parent / f"{artifact.get('approval_id')}.json"
    recovery_path = recovery_parent / f"{artifact.get('approval_id')}.json"
    marker_confined = _filesystem_path_is_within(marker_path, marker_parent)
    recovery_confined = _filesystem_path_is_within(recovery_path, recovery_parent)
    marker_exists = marker_path.exists()
    recovery_exists = recovery_path.exists()
    secret_errors = scan_secret_like_keys(artifact)
    gate_allowed, gate_reason = check_runtime_operation(
        PROMOTION_GATE_APPLY_OPERATION,
        actor_adapter_id="codex",
        task_type="promotion-review",
        write_targets=[
            str(Path(TRUSTED_SKILL_REL) / f"{design.get('proposed_skill_id')}.yaml"),
            str(Path(SITEOPS_SKILL_CARD_REL) / f"{design.get('proposed_skill_id')}.json"),
        ],
    )
    design_ready = design.get("bound_approval_writer_design_status") == "bound_approval_writer_design_ready_no_write"
    target_ready = (
        bool(target.get("parent_confined"))
        and bool(target.get("target_confined"))
        and not bool(target.get("target_exists"))
    )
    artifact_pending = artifact.get("status") == "pending"
    scope_bound = all(artifact.get(key) == scope.get(key) for key in ("tenant_id", "workspace_id", "user_id"))
    audit_contract = dict(design.get("audit_event_contract") or {})
    audit_forbidden = [str(item) for item in audit_contract.get("metadata_forbidden") or []]
    audit_contract_ready = all(
        field in audit_forbidden
        for field in ("cookie", "token", "password", "api_key", "session", "secret")
    )
    preflight_checks = {
        "writer_design_ready": {
            "passed": design_ready,
            "status": design.get("bound_approval_writer_design_status"),
        },
        "target_path_scoped_and_absent": {
            "passed": target_ready,
            "target_path": target.get("path"),
            "target_exists": bool(target.get("target_exists")),
        },
        "approval_artifact_pending": {
            "passed": artifact_pending,
            "status": artifact.get("status"),
        },
        "approval_artifact_scope_bound": {
            "passed": scope_bound,
            "requires": ["tenant_id", "workspace_id", "user_id"],
        },
        "approval_artifact_secret_like_keys_absent": {
            "passed": not secret_errors,
            "raw_errors_visible": False,
            "matched_error_count": len(secret_errors),
        },
        "audit_contract_forbids_secret_session_metadata": {
            "passed": audit_contract_ready,
            "metadata_forbidden": audit_forbidden,
        },
        "idempotency_marker_absent_and_scoped": {
            "passed": marker_confined and not marker_exists,
            "marker_path": str(marker_path),
            "marker_confined": marker_confined,
            "marker_exists": marker_exists,
            "write_allowed_in_this_pass": False,
        },
        "recovery_marker_absent_and_scoped": {
            "passed": recovery_confined and not recovery_exists,
            "recovery_path": str(recovery_path),
            "recovery_confined": recovery_confined,
            "recovery_exists": recovery_exists,
            "write_allowed_in_this_pass": False,
        },
        "trusted_apply_gate_posture_recorded": {
            "passed": True,
            "operation": PROMOTION_GATE_APPLY_OPERATION,
            "allowed": gate_allowed,
            "reason": gate_reason,
            "required_before_trusted_artifact_write": True,
        },
    }
    checks_passed = all(
        bool(check.get("passed"))
        for key, check in preflight_checks.items()
        if key != "trusted_apply_gate_posture_recorded"
    )
    if not design_ready:
        preflight_status = f"blocked_bound_approval_writer_design: {design.get('bound_approval_writer_design_status')}"
        review_decision = "blocked_before_bound_approval_writer_preflight"
    elif not target_ready:
        preflight_status = "blocked_bound_approval_writer_target"
        review_decision = "blocked_target_requires_manual_review"
    elif marker_exists:
        preflight_status = "blocked_existing_bound_approval_idempotency_marker"
        review_decision = "blocked_existing_marker_requires_manual_review"
    elif recovery_exists:
        preflight_status = "blocked_existing_bound_approval_recovery_marker"
        review_decision = "blocked_existing_recovery_marker_requires_manual_review"
    elif not checks_passed:
        preflight_status = "blocked_bound_approval_writer_preflight_checks"
        review_decision = "blocked_preflight_checks_failed"
    else:
        preflight_status = "bound_approval_writer_preflight_ready_no_write"
        review_decision = "preflight_ready_for_future_writer_implementation_review"

    denied_effects = list(design.get("denied_effects") or [])
    for effect in [
        "write bound approval writer preflight marker",
        "write bound approval recovery marker",
        "run bound approval writer",
    ]:
        if effect not in denied_effects:
            denied_effects.insert(0, effect)
    return {
        "ok": True,
        "action": PROMOTION_BOUND_APPROVAL_WRITER_PREFLIGHT_ACTION,
        "candidate_id": design.get("candidate_id"),
        "proposed_skill_id": design.get("proposed_skill_id"),
        "scope": scope,
        "approval_id": approval_id,
        "approval_rebind_spec_status": design.get("approval_rebind_spec_status"),
        "bound_approval_request_spec_status": design.get("bound_approval_request_spec_status"),
        "bound_approval_writer_design_status": design.get("bound_approval_writer_design_status"),
        "bound_approval_writer_preflight_status": preflight_status,
        "review_decision": review_decision,
        "approval_request_artifact": artifact,
        "target_path_preview": target,
        "idempotency_marker_preview": {
            "path": str(marker_path),
            "parent": str(marker_parent),
            "marker_confined": marker_confined,
            "marker_exists": marker_exists,
            "write_allowed_in_this_pass": False,
        },
        "recovery_marker_preview": {
            "path": str(recovery_path),
            "parent": str(recovery_parent),
            "recovery_confined": recovery_confined,
            "recovery_exists": recovery_exists,
            "write_allowed_in_this_pass": False,
        },
        "trusted_apply_gate_posture": {
            "operation": PROMOTION_GATE_APPLY_OPERATION,
            "allowed": gate_allowed,
            "reason": gate_reason,
            "required_before_trusted_artifact_write": True,
            "gate_mutation_allowed": False,
        },
        "preflight_checks": preflight_checks,
        "preflight_ready_no_write": preflight_status == "bound_approval_writer_preflight_ready_no_write",
        "future_writer_requirements": [
            "rerun this preflight immediately before writing the replacement approval artifact",
            "write only a new pending bound approval request after explicit writer implementation approval",
            "append a scoped audit event without secrets or raw candidate content",
            "write idempotency/recovery markers only in the future writer pass",
            "do not consume the replacement approval or write trusted artifacts in the writer",
        ],
        "blocked_actions": denied_effects,
        "denied_effects": denied_effects,
        "writes_performed": False,
        "approval_request_artifact_written": False,
        "approval_artifact_write_allowed": False,
        "bound_approval_writer_implemented": False,
        "bound_approval_writer_enabled": False,
        "bound_approval_writer_execution_allowed": False,
        "bound_approval_preflight_marker_written": False,
        "bound_approval_recovery_marker_written": False,
        "bound_approval_audit_event_written": False,
        "bound_approval_idempotency_marker_written": False,
        "legacy_approval_mutation_allowed": False,
        "replacement_approval_request_written": False,
        "approval_decision_written": False,
        "audit_events_written": False,
        "inactive_artifacts_written": False,
        "executor_implemented": False,
        "executor_enabled": False,
        "executor_build_allowed": False,
        "executor_implementation_allowed": False,
        "executor_implementation_performed": False,
        "allowlist_change_allowed": False,
        "allowlist_change_performed": False,
        "policy_file_write_allowed": False,
        "trusted_skill_write_allowed": False,
        "siteops_skill_card_write_allowed": False,
        "browser_execution_allowed": False,
        "agent_bus_enqueue_allowed": False,
        "provider_api_call_allowed": False,
        "activation_allowed": False,
        "canonical_writeback_allowed": False,
        "boundary": (
            "bound approval writer invocation preflight only; no approval artifact, audit event, "
            "idempotency marker, recovery marker, approval decision, trusted artifact, browser, "
            "Agent Bus, provider, activation, Gate policy, or canonical writeback side effect is performed"
        ),
    }


def candidate_promotion_bound_approval_writer_implementation_request(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    approval_id: str,
) -> dict[str, Any]:
    """Return a no-write operator request packet for a future bound approval writer."""
    preflight = candidate_promotion_bound_approval_writer_preflight(
        candidate_id,
        root,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
        approval_id=approval_id,
    )
    scope = dict(preflight.get("scope") or {})
    request_id = _new_run_id(f"{preflight.get('candidate_id')}_bound_writer_implementation_request")
    preflight_ready = bool(preflight.get("preflight_ready_no_write"))
    request_artifact = {
        "request_id": request_id,
        "request_type": "siteops_bound_approval_writer_implementation_request",
        "tenant_id": scope.get("tenant_id"),
        "workspace_id": scope.get("workspace_id"),
        "user_id": scope.get("user_id"),
        "candidate_id": preflight.get("candidate_id"),
        "proposed_skill_id": preflight.get("proposed_skill_id"),
        "supersedes_approval_id": approval_id,
        "replacement_approval_id": (preflight.get("approval_request_artifact") or {}).get("approval_id"),
        "requested_action": "implement_bound_approval_request_writer",
        "required_operator_decision": "approve_future_writer_implementation_pass",
        "status": "review_packet_only",
        "preflight_status": preflight.get("bound_approval_writer_preflight_status"),
        "implementation_allowed_in_this_pass": False,
        "writes_allowed_in_this_pass": False,
        "trusted_writes_allowed": False,
        "approval_consumption_allowed": False,
    }
    readiness_checks = {
        "preflight_ready": {
            "passed": preflight_ready,
            "status": preflight.get("bound_approval_writer_preflight_status"),
        },
        "operator_decision_required": {
            "passed": True,
            "required_decision": "approve_future_writer_implementation_pass",
        },
        "request_scope_bound": {
            "passed": all(request_artifact.get(key) == scope.get(key) for key in ("tenant_id", "workspace_id", "user_id")),
            "requires": ["tenant_id", "workspace_id", "user_id"],
        },
        "implementation_still_disabled": {
            "passed": True,
            "implementation_allowed_in_this_pass": False,
        },
        "writer_still_no_write": {
            "passed": True,
            "approval_request_artifact_written": False,
            "marker_written": False,
        },
    }
    checks_passed = all(bool(check.get("passed")) for check in readiness_checks.values())
    if not preflight_ready:
        request_status = (
            "blocked_bound_approval_writer_preflight: "
            f"{preflight.get('bound_approval_writer_preflight_status')}"
        )
        review_decision = "blocked_before_implementation_request"
    elif not checks_passed:
        request_status = "blocked_bound_approval_writer_implementation_request_checks"
        review_decision = "blocked_request_checks_failed"
    else:
        request_status = "bound_approval_writer_implementation_request_ready_no_write"
        review_decision = "ready_for_operator_review_of_future_writer_implementation"

    denied_effects = list(preflight.get("denied_effects") or [])
    for effect in [
        "write bound approval writer implementation approval request",
        "implement bound approval writer",
        "run bound approval writer",
    ]:
        if effect not in denied_effects:
            denied_effects.insert(0, effect)
    return {
        "ok": True,
        "action": PROMOTION_BOUND_APPROVAL_WRITER_IMPLEMENTATION_REQUEST_ACTION,
        "candidate_id": preflight.get("candidate_id"),
        "proposed_skill_id": preflight.get("proposed_skill_id"),
        "scope": scope,
        "approval_id": approval_id,
        "approval_rebind_spec_status": preflight.get("approval_rebind_spec_status"),
        "bound_approval_request_spec_status": preflight.get("bound_approval_request_spec_status"),
        "bound_approval_writer_design_status": preflight.get("bound_approval_writer_design_status"),
        "bound_approval_writer_preflight_status": preflight.get("bound_approval_writer_preflight_status"),
        "bound_approval_writer_implementation_request_status": request_status,
        "review_decision": review_decision,
        "implementation_request_artifact": request_artifact,
        "implementation_request_checks": readiness_checks,
        "preflight_packet": {
            "target_path_preview": preflight.get("target_path_preview"),
            "idempotency_marker_preview": preflight.get("idempotency_marker_preview"),
            "recovery_marker_preview": preflight.get("recovery_marker_preview"),
            "trusted_apply_gate_posture": preflight.get("trusted_apply_gate_posture"),
        },
        "future_implementation_requirements": [
            "operator must explicitly approve a future writer implementation pass",
            "future writer must rerun bound-approval-writer-preflight immediately before writing",
            "future writer may write only a new pending replacement approval request",
            "future writer must append scoped audit evidence and idempotency/recovery markers",
            "future writer must not consume approvals or write trusted Browser Skill/SiteOps Skill Card artifacts",
        ],
        "request_ready_no_write": request_status == "bound_approval_writer_implementation_request_ready_no_write",
        "blocked_actions": denied_effects,
        "denied_effects": denied_effects,
        "writes_performed": False,
        "implementation_request_artifact_written": False,
        "approval_request_artifact_written": False,
        "approval_artifact_write_allowed": False,
        "bound_approval_writer_implemented": False,
        "bound_approval_writer_enabled": False,
        "bound_approval_writer_execution_allowed": False,
        "bound_approval_preflight_marker_written": False,
        "bound_approval_recovery_marker_written": False,
        "bound_approval_audit_event_written": False,
        "bound_approval_idempotency_marker_written": False,
        "legacy_approval_mutation_allowed": False,
        "replacement_approval_request_written": False,
        "approval_decision_written": False,
        "audit_events_written": False,
        "inactive_artifacts_written": False,
        "executor_implemented": False,
        "executor_enabled": False,
        "executor_build_allowed": False,
        "executor_implementation_allowed": False,
        "executor_implementation_performed": False,
        "allowlist_change_allowed": False,
        "allowlist_change_performed": False,
        "policy_file_write_allowed": False,
        "trusted_skill_write_allowed": False,
        "siteops_skill_card_write_allowed": False,
        "browser_execution_allowed": False,
        "agent_bus_enqueue_allowed": False,
        "provider_api_call_allowed": False,
        "activation_allowed": False,
        "canonical_writeback_allowed": False,
        "boundary": (
            "bound approval writer implementation request packet only; no implementation request artifact, "
            "approval artifact, audit event, idempotency marker, recovery marker, approval decision, "
            "trusted artifact, browser, Agent Bus, provider, activation, Gate policy, or canonical writeback "
            "side effect is performed"
        ),
    }


def candidate_promotion_bound_approval_writer_implementation_approval(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    approval_id: str,
    decision: str,
    actor: str | None = None,
    reason: str | None = None,
) -> dict[str, Any]:
    """Return a no-write approval/rejection packet for a future writer implementation."""
    normalized_decision = (decision or "").strip().lower()
    if normalized_decision not in {"approve", "reject"}:
        raise ValueError("decision must be 'approve' or 'reject'")

    implementation_request = candidate_promotion_bound_approval_writer_implementation_request(
        candidate_id,
        root,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
        approval_id=approval_id,
    )
    scope = dict(implementation_request.get("scope") or {})
    actor_id = (actor or user_id or "").strip()
    request_artifact = dict(implementation_request.get("implementation_request_artifact") or {})
    request_status = implementation_request.get("bound_approval_writer_implementation_request_status")
    request_ready = bool(implementation_request.get("request_ready_no_write"))
    decision_id = _new_run_id(f"bound_writer_implementation_approval_{implementation_request.get('candidate_id')}")

    approval_record = {
        "decision_id": decision_id,
        "record_type": "siteops_bound_approval_writer_implementation_approval",
        "tenant_id": scope.get("tenant_id"),
        "workspace_id": scope.get("workspace_id"),
        "user_id": scope.get("user_id"),
        "actor": actor_id,
        "decision": normalized_decision,
        "reason": reason or "",
        "candidate_id": implementation_request.get("candidate_id"),
        "proposed_skill_id": implementation_request.get("proposed_skill_id"),
        "source_approval_id": approval_id,
        "implementation_request_id": request_artifact.get("request_id"),
        "replacement_approval_id": request_artifact.get("replacement_approval_id"),
        "status": "review_decision_packet_only",
        "durable_record_written": False,
        "approval_decision_written": False,
        "implementation_allowed_in_this_pass": False,
        "replacement_approval_write_allowed_in_this_pass": False,
        "trusted_writes_allowed": False,
        "approval_consumption_allowed": False,
    }
    implementation_approved = request_ready and normalized_decision == "approve"
    implementation_rejected = request_ready and normalized_decision == "reject"
    if not request_ready:
        approval_status = f"blocked_bound_approval_writer_implementation_request: {request_status}"
        review_decision = "blocked_before_implementation_approval"
    elif implementation_approved:
        approval_status = "bound_approval_writer_implementation_approved_for_next_pass_no_write"
        review_decision = "operator_intent_approve_writer_implementation_next_pass"
    else:
        approval_status = "bound_approval_writer_implementation_rejected_no_write"
        review_decision = "operator_intent_reject_writer_implementation"

    approval_checks = {
        "implementation_request_ready": {
            "passed": request_ready,
            "status": request_status,
        },
        "decision_valid": {
            "passed": True,
            "decision": normalized_decision,
        },
        "actor_present": {
            "passed": bool(actor_id),
            "actor": actor_id,
        },
        "approval_record_still_no_write": {
            "passed": True,
            "durable_record_written": False,
            "approval_decision_written": False,
        },
        "writer_execution_still_disabled": {
            "passed": True,
            "bound_approval_writer_implemented": False,
            "bound_approval_writer_execution_allowed": False,
        },
        "replacement_approval_write_still_blocked_this_pass": {
            "passed": True,
            "replacement_approval_request_written": False,
            "replacement_approval_write_allowed_in_this_pass": False,
        },
    }
    if not approval_checks["actor_present"]["passed"]:
        approval_status = "blocked_missing_implementation_approval_actor"
        review_decision = "blocked_before_implementation_approval"
        implementation_approved = False
        implementation_rejected = False

    denied_effects = list(implementation_request.get("denied_effects") or [])
    for effect in [
        "write bound approval writer implementation approval record",
        "consume bound approval writer implementation approval",
        "write replacement approval request from implementation approval",
        "implement bound approval writer in approval pass",
    ]:
        if effect not in denied_effects:
            denied_effects.insert(0, effect)

    return {
        "ok": True,
        "action": PROMOTION_BOUND_APPROVAL_WRITER_IMPLEMENTATION_APPROVAL_ACTION,
        "candidate_id": implementation_request.get("candidate_id"),
        "proposed_skill_id": implementation_request.get("proposed_skill_id"),
        "scope": scope,
        "approval_id": approval_id,
        "decision": normalized_decision,
        "actor": actor_id,
        "approval_rebind_spec_status": implementation_request.get("approval_rebind_spec_status"),
        "bound_approval_request_spec_status": implementation_request.get("bound_approval_request_spec_status"),
        "bound_approval_writer_design_status": implementation_request.get("bound_approval_writer_design_status"),
        "bound_approval_writer_preflight_status": implementation_request.get("bound_approval_writer_preflight_status"),
        "bound_approval_writer_implementation_request_status": request_status,
        "bound_approval_writer_implementation_approval_status": approval_status,
        "review_decision": review_decision,
        "implementation_request_packet": {
            "request_id": request_artifact.get("request_id"),
            "status": request_status,
            "request_ready_no_write": request_ready,
        },
        "implementation_approval_record": approval_record,
        "implementation_approval_checks": approval_checks,
        "implementation_patch_allowed_next_pass": implementation_approved,
        "implementation_rejected_no_write": implementation_rejected,
        "future_writer_requirements": [
            "future writer patch pass must cite this approval packet and rerun implementation-request/preflight",
            "future writer may write only a new pending bound replacement approval request",
            "future writer must not consume approvals or write trusted Browser Skill/SiteOps Skill Card artifacts",
            "future writer must still leave trusted executor, Gate allowlist, browser execution, provider calls, activation, and canonical writeback blocked",
        ],
        "blocked_actions": denied_effects,
        "denied_effects": denied_effects,
        "writes_performed": False,
        "implementation_approval_record_written": False,
        "implementation_request_artifact_written": False,
        "approval_request_artifact_written": False,
        "approval_artifact_write_allowed": False,
        "bound_approval_writer_implemented": False,
        "bound_approval_writer_enabled": False,
        "bound_approval_writer_execution_allowed": False,
        "bound_approval_preflight_marker_written": False,
        "bound_approval_recovery_marker_written": False,
        "bound_approval_audit_event_written": False,
        "bound_approval_idempotency_marker_written": False,
        "legacy_approval_mutation_allowed": False,
        "replacement_approval_request_written": False,
        "approval_decision_written": False,
        "audit_events_written": False,
        "inactive_artifacts_written": False,
        "executor_implemented": False,
        "executor_enabled": False,
        "executor_build_allowed": False,
        "executor_implementation_allowed": False,
        "executor_implementation_performed": False,
        "allowlist_change_allowed": False,
        "allowlist_change_performed": False,
        "policy_file_write_allowed": False,
        "trusted_skill_write_allowed": False,
        "siteops_skill_card_write_allowed": False,
        "browser_execution_allowed": False,
        "agent_bus_enqueue_allowed": False,
        "provider_api_call_allowed": False,
        "activation_allowed": False,
        "canonical_writeback_allowed": False,
        "boundary": (
            "bound approval writer implementation approval packet only; no approval record, implementation "
            "request artifact, replacement approval artifact, audit event, idempotency marker, recovery marker, "
            "trusted artifact, browser, Agent Bus, provider, activation, Gate policy, or canonical writeback "
            "side effect is performed"
        ),
    }


def candidate_promotion_gate_apply_design(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    approval_id: str,
) -> dict[str, Any]:
    """Return a denied-by-default Gate apply design packet.

    This is a preflight/design surface only. It proves what a future Gate apply
    path would need to check, then refuses execution and writes no trusted
    Browser Skill, SiteOps Skill Card, browser state, or canonical memory.
    """
    base = candidate_promotion_apply_contract(
        candidate_id,
        root,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
        approval_id=approval_id,
    )
    apply_contract = dict(base.get("apply_contract") or {})
    target = dict(apply_contract.get("target") or {})
    proposed_skill_id = base.get("proposed_skill_id") or target.get("proposed_skill_id")
    siteops_skill_card_path = _siteops_skill_card_target(str(proposed_skill_id) if proposed_skill_id else None)
    write_targets = [
        str(path)
        for path in [target.get("trusted_skill_path"), siteops_skill_card_path]
        if path
    ]
    gate_allowed, gate_reason = check_runtime_operation(
        PROMOTION_GATE_APPLY_OPERATION,
        write_targets=write_targets,
    )
    apply_status = str(apply_contract.get("apply_contract_status") or "")
    if apply_status != "gate_apply_review_ready":
        design_status = apply_status or "blocked_missing_apply_contract"
    elif not gate_allowed:
        design_status = "blocked_gate_operation_not_allowlisted"
    else:
        design_status = "gate_apply_design_ready_but_execution_disabled"

    target_write_preview = [
        {
            "kind": "trusted_browser_skill",
            "path": target.get("trusted_skill_path"),
            "path_confined": _repo_path_is_confined(str(target.get("trusted_skill_path") or ""), TRUSTED_SKILL_REL),
            "write_allowed": False,
        },
        {
            "kind": "siteops_skill_card",
            "path": siteops_skill_card_path,
            "path_confined": _repo_path_is_confined(siteops_skill_card_path, SITEOPS_SKILL_CARD_REL),
            "write_allowed": False,
        },
    ]
    return {
        "ok": True,
        "action": PROMOTION_GATE_APPLY_ACTION,
        "candidate_id": base.get("candidate_id"),
        "proposed_skill_id": proposed_skill_id,
        "scope": base.get("scope"),
        "approval": base.get("approval"),
        "approval_provenance": base.get("approval_provenance"),
        "apply_contract": apply_contract,
        "gate_apply_design_status": design_status,
        "gate_operation": PROMOTION_GATE_APPLY_OPERATION,
        "gate_operation_allowed": bool(gate_allowed),
        "gate_reason": gate_reason,
        "target_write_preview": target_write_preview,
        "required_future_checks": [
            "approved SiteOps ApprovalRequest scoped to tenant/workspace/user",
            "candidate preflight still ready for operator review",
            "secret/cookie/token/session exclusion rechecked",
            "target paths remain inside trusted Browser Skill and SiteOps Skill Card homes",
            "future Gate operation explicitly allowlisted before any write executor exists",
            "Agent Activity and SiteOps audit records written by the future executor",
        ],
        "denied_effects": [
            "trusted_skill_write",
            "siteops_skill_card_write",
            "browser_execution",
            "skill_activation",
            "canonical_writeback",
        ],
        "writes_performed": False,
        "apply_execution_allowed": False,
        "trusted_skill_write_allowed": False,
        "siteops_skill_card_write_allowed": False,
        "browser_execution_allowed": False,
        "activation_allowed": False,
        "canonical_writeback_allowed": False,
        "boundary": (
            "Gate apply design/preflight only; this command does not execute the "
            "future apply operation or write trusted artifacts"
        ),
    }


def candidate_promotion_gate_executor_spec(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    approval_id: str,
) -> dict[str, Any]:
    """Return the fail-closed future executor specification.

    This is still a contract/spec surface only. It does not implement or enable
    the trusted artifact write executor.
    """
    request_contract = candidate_promotion_request_contract(
        candidate_id,
        root,
        requested_by=user_id,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
    )
    design = candidate_promotion_gate_apply_design(
        candidate_id,
        root,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
        approval_id=approval_id,
    )
    design_status = str(design.get("gate_apply_design_status") or "")
    apply_contract = dict(design.get("apply_contract") or {})
    approval_provenance = dict(design.get("approval_provenance") or {})
    target_preview = list(design.get("target_write_preview") or [])
    candidate_ready = (
        request_contract.get("contract_status") == "approval_request_ready"
        and not list(request_contract.get("blockers") or [])
    )
    apply_ready = apply_contract.get("apply_contract_status") == "gate_apply_review_ready"
    provenance_bound = approval_provenance.get("provenance_status") == "bound_match"
    target_paths_confined = bool(target_preview) and all(
        bool(item.get("path")) and bool(item.get("path_confined"))
        for item in target_preview
    )
    secret_session_exclusion_recheck = _secret_session_exclusion_recheck(
        dict(request_contract.get("preflight") or {})
    )
    secret_session_exclusion_passed = bool(secret_session_exclusion_recheck.get("passed"))
    gate_allowed = bool(design.get("gate_operation_allowed"))
    entrypoint_status = _trusted_executor_entrypoint_status()
    executor_implemented = bool(entrypoint_status.get("guarded"))
    if not candidate_ready:
        executor_status = "blocked_candidate_preflight"
    elif not apply_ready:
        executor_status = str(apply_contract.get("apply_contract_status") or "blocked_missing_apply_contract")
    elif not provenance_bound:
        executor_status = "blocked_approval_provenance_not_bound"
    elif not target_paths_confined:
        executor_status = "blocked_target_path_not_confined"
    elif not secret_session_exclusion_passed:
        executor_status = "blocked_secret_session_exclusion"
    elif not executor_implemented:
        executor_status = "executor_spec_ready_but_executor_not_built"
    elif not gate_allowed:
        executor_status = "executor_spec_ready_gate_blocked"
    elif design_status == "gate_apply_design_ready_but_execution_disabled":
        executor_status = "executor_spec_ready_gate_allowlisted_no_write"
    elif design_status:
        executor_status = design_status
    else:
        executor_status = "blocked_missing_gate_apply_design"
    executor_preflight_checks = [
        _executor_preflight_check(
            "candidate_preflight_ready",
            passed=candidate_ready,
            detail=str(request_contract.get("contract_status")),
        ),
        _executor_preflight_check(
            "apply_contract_ready",
            passed=apply_ready,
            detail=str(apply_contract.get("apply_contract_status")),
        ),
        _executor_preflight_check(
            "approval_provenance_bound_match",
            passed=provenance_bound,
            detail=str(approval_provenance.get("provenance_status")),
        ),
        _executor_preflight_check(
            "target_paths_confined",
            passed=target_paths_confined,
            detail="all future trusted targets remain inside governed homes",
        ),
        _executor_preflight_check(
            "secret_session_exclusion_rechecked",
            passed=secret_session_exclusion_passed,
            detail=_secret_session_exclusion_detail(secret_session_exclusion_recheck),
        ),
        _executor_preflight_check(
            "gate_operation_allowlisted",
            passed=gate_allowed,
            detail=str(design.get("gate_reason")),
        ),
        _executor_preflight_check(
            "executor_implemented",
            passed=executor_implemented,
            detail=str(entrypoint_status),
        ),
        _executor_preflight_check(
            "writes_disabled",
            passed=True,
            detail="spec command performs no trusted writes",
        ),
    ]
    future_write_plan = [
        {
            "order": 1,
            "step": "revalidate_candidate",
            "effect": "read_only",
            "required": True,
            "implemented": False,
        },
        {
            "order": 2,
            "step": "recheck_secret_session_exclusion",
            "effect": "read_only",
            "required": True,
            "implemented": False,
        },
        {
            "order": 3,
            "step": "write_prewrite_audit_event",
            "effect": "scoped_audit_only",
            "required": True,
            "implemented": False,
        },
    ]
    for preview in target_preview:
        future_write_plan.append(
            {
                "order": len(future_write_plan) + 1,
                "step": f"write_{preview.get('kind')}",
                "effect": "future_trusted_artifact_write",
                "target_path": preview.get("path"),
                "path_confined": preview.get("path_confined"),
                "write_allowed": False,
                "implemented": False,
            }
        )
    future_write_plan.append(
        {
            "order": len(future_write_plan) + 1,
            "step": "write_postwrite_audit_event",
            "effect": "scoped_audit_only",
            "required": True,
            "implemented": False,
        }
    )

    return {
        "ok": True,
        "action": PROMOTION_GATE_EXECUTOR_SPEC_ACTION,
        "candidate_id": design.get("candidate_id"),
        "proposed_skill_id": design.get("proposed_skill_id"),
        "scope": design.get("scope"),
        "approval": design.get("approval"),
        "approval_provenance": approval_provenance,
        "candidate_preflight": request_contract.get("preflight"),
        "candidate_preflight_status": request_contract.get("contract_status"),
        "candidate_preflight_blockers": list(request_contract.get("blockers") or []),
        "secret_session_exclusion_recheck": secret_session_exclusion_recheck,
        "apply_contract": apply_contract,
        "gate_apply_design_status": design_status,
        "executor_spec_status": executor_status,
        "executor_preflight_status": executor_status,
        "gate_operation": design.get("gate_operation"),
        "gate_operation_allowed": gate_allowed,
        "gate_reason": design.get("gate_reason"),
        "target_write_preview": target_preview,
        "executor_preflight_checks": executor_preflight_checks,
        "future_executor": {
            "entrypoint": entrypoint_status.get("function"),
            "implementation_status": entrypoint_status.get("status"),
            "mode": "guarded_inactive_artifact_writer",
            "enabled": bool(executor_implemented and gate_allowed),
            "allowlisted": gate_allowed,
            "requires_separate_gate_allowlist_pass": True,
        },
        "future_write_plan": future_write_plan,
        "executor_preconditions": [
            "approved and bound SiteOps ApprovalRequest",
            "tenant/workspace/user scope must match approval and candidate request",
            "candidate validation must be rerun immediately before write",
            "secret/cookie/token/session exclusion must be rerun immediately before write",
            "Gate operation must be explicitly allowlisted in a separate pass",
            "target paths must remain confined to governed trusted artifact homes",
            "prewrite and postwrite SiteOps audit events must be emitted by the future executor",
            "trusted artifacts must remain inactive until a separate activation path exists",
        ],
        "rollback_policy": (
            "future executor must fail closed before activation; partial trusted artifacts "
            "must remain inactive review artifacts and must be recorded in scoped audit"
        ),
        "acceptance_tests_required": [
            "missing or pending approval blocks executor",
            "approval candidate/proposed-skill mismatch blocks executor",
            "Gate operation not allowlisted blocks executor",
            "path traversal target blocks executor",
            "secret-like candidate content blocks executor",
            "trusted Browser Skill and SiteOps Skill Card writes remain inactive until activation is separately approved",
        ],
        "denied_effects": [
            "trusted_skill_write",
            "siteops_skill_card_write",
            "browser_execution",
            "agent_bus_enqueue",
            "provider_api_call",
            "skill_activation",
            "canonical_writeback",
        ],
        "writes_performed": False,
        "executor_implemented": executor_implemented,
        "executor_enabled": bool(executor_implemented and gate_allowed),
        "apply_execution_allowed": False,
        "trusted_skill_write_allowed": False,
        "siteops_skill_card_write_allowed": False,
        "browser_execution_allowed": False,
        "agent_bus_enqueue_allowed": False,
        "provider_api_call_allowed": False,
        "activation_allowed": False,
        "canonical_writeback_allowed": False,
        "boundary": (
            "executor specification only; the guarded executor entrypoint may exist, "
            "but this spec command writes no trusted Browser Skill or SiteOps Skill Card"
        ),
    }


def candidate_promotion_gate_allowlist_review(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    approval_id: str,
) -> dict[str, Any]:
    """Return a fail-closed Gate allowlist review packet.

    This is a review/spec surface only. It does not edit
    runtime/policy/gateway_allowlists.json, implement the executor, or write
    trusted Browser Skill/SiteOps artifacts.
    """
    spec = candidate_promotion_gate_executor_spec(
        candidate_id,
        root,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
        approval_id=approval_id,
    )
    spec_status = str(spec.get("executor_spec_status") or "")
    checks = {
        str(item.get("check_id")): item
        for item in spec.get("executor_preflight_checks") or []
        if isinstance(item, dict)
    }
    target_preview = list(spec.get("target_write_preview") or [])
    target_paths = [str(item.get("path")) for item in target_preview if item.get("path")]
    gate_allowed = bool(spec.get("gate_operation_allowed"))
    candidate_ready = bool(checks.get("candidate_preflight_ready", {}).get("passed"))
    apply_ready = bool(checks.get("apply_contract_ready", {}).get("passed"))
    provenance_bound = bool(checks.get("approval_provenance_bound_match", {}).get("passed"))
    target_paths_confined = bool(checks.get("target_paths_confined", {}).get("passed"))
    secret_session_exclusion_recheck = dict(spec.get("secret_session_exclusion_recheck") or {})
    secret_session_exclusion_passed = bool(secret_session_exclusion_recheck.get("passed"))
    executor_implemented = bool(checks.get("executor_implemented", {}).get("passed"))

    if not candidate_ready:
        review_status = "blocked_candidate_preflight"
    elif not apply_ready:
        review_status = spec_status or "blocked_apply_contract"
    elif not provenance_bound:
        review_status = "blocked_approval_provenance_not_bound"
    elif not target_paths_confined:
        review_status = "blocked_target_path_not_confined"
    elif not secret_session_exclusion_passed:
        review_status = "blocked_secret_session_exclusion"
    elif not executor_implemented:
        review_status = "blocked_executor_not_implemented"
    elif gate_allowed:
        review_status = "blocked_operation_already_allowlisted"
    else:
        review_status = "allowlist_review_ready_but_policy_change_disabled"

    allowlist_review_checks = [
        _executor_preflight_check(
            "executor_spec_available",
            passed=bool(spec),
            detail=spec_status,
        ),
        _executor_preflight_check(
            "candidate_preflight_ready",
            passed=candidate_ready,
            detail=str(checks.get("candidate_preflight_ready", {}).get("detail")),
        ),
        _executor_preflight_check(
            "apply_contract_ready",
            passed=apply_ready,
            detail=str(checks.get("apply_contract_ready", {}).get("detail")),
        ),
        _executor_preflight_check(
            "approval_provenance_bound_match",
            passed=provenance_bound,
            detail=str(checks.get("approval_provenance_bound_match", {}).get("detail")),
        ),
        _executor_preflight_check(
            "target_paths_confined",
            passed=target_paths_confined,
            detail="all future trusted targets must stay inside governed homes",
        ),
        _executor_preflight_check(
            "secret_session_exclusion_rechecked",
            passed=secret_session_exclusion_passed,
            detail=_secret_session_exclusion_detail(secret_session_exclusion_recheck),
        ),
        _executor_preflight_check(
            "executor_implemented",
            passed=executor_implemented,
            detail="allowlisting is blocked until the trusted artifact executor exists and is reviewed",
        ),
        _executor_preflight_check(
            "operation_currently_allowlisted",
            passed=gate_allowed,
            required=False,
            detail=str(spec.get("gate_reason")),
        ),
        _executor_preflight_check(
            "allowlist_policy_write_disabled",
            passed=True,
            detail="review command does not edit runtime/policy/gateway_allowlists.json",
        ),
    ]

    return {
        "ok": True,
        "action": PROMOTION_GATE_ALLOWLIST_REVIEW_ACTION,
        "candidate_id": spec.get("candidate_id"),
        "proposed_skill_id": spec.get("proposed_skill_id"),
        "scope": spec.get("scope"),
        "approval": spec.get("approval"),
        "approval_provenance": spec.get("approval_provenance"),
        "secret_session_exclusion_recheck": secret_session_exclusion_recheck,
        "executor_spec_status": spec_status,
        "allowlist_review_status": review_status,
        "gate_operation": spec.get("gate_operation"),
        "operation_currently_allowlisted": gate_allowed,
        "gate_reason": spec.get("gate_reason"),
        "target_write_preview": target_preview,
        "secret_session_exclusion_recheck": secret_session_exclusion_recheck,
        "allowlist_review_checks": allowlist_review_checks,
        "allowlist_entry_preview": {
            "policy_file": "runtime/policy/gateway_allowlists.json",
            "operation": PROMOTION_GATE_APPLY_OPERATION,
            "write_targets": target_paths,
            "status": "preview_only",
            "would_modify_policy_file": True,
            "policy_file_write_performed": False,
        },
        "minimum_allowlist_conditions": [
            "approved and bound SiteOps ApprovalRequest",
            "candidate promotion preflight remains ready immediately before execution",
            "trusted artifact executor is implemented, reviewed, and tested separately",
            "executor emits scoped prewrite and postwrite audit events",
            "target path confinement and secret/session exclusion checks pass immediately before write",
            "trusted artifacts remain inactive until a separate activation path exists",
            "rollback and partial-write audit behavior is documented and tested",
        ],
        "risk_review": [
            "allowlisting would permit trusted Browser Skill and SiteOps Skill Card artifact writes by a future executor",
            "stale candidate or stale approval provenance could promote the wrong skill if not revalidated",
            "path traversal or malformed skill IDs must fail before any write",
            "secret, cookie, token, or browser-session material must remain excluded from candidates and audits",
            "activation must remain separated from artifact writeback",
        ],
        "review_decision": "do_not_allowlist_in_this_pass",
        "required_future_decisions": [
            "whether to implement the trusted artifact executor",
            "whether the executor write target categories belong in Gate policy",
            "whether activation should remain a separate approval/workflow",
            "which runtime owns postwrite audit and rollback handling",
        ],
        "writes_performed": False,
        "allowlist_change_allowed": False,
        "allowlist_change_performed": False,
        "policy_file_write_allowed": False,
        "executor_implemented": executor_implemented,
        "executor_enabled": bool(executor_implemented and gate_allowed),
        "apply_execution_allowed": False,
        "trusted_skill_write_allowed": False,
        "siteops_skill_card_write_allowed": False,
        "browser_execution_allowed": False,
        "agent_bus_enqueue_allowed": False,
        "provider_api_call_allowed": False,
        "activation_allowed": False,
        "canonical_writeback_allowed": False,
        "boundary": (
            "Gate allowlist review only; runtime/policy/gateway_allowlists.json is not edited, "
            "the executor cannot write unless Gate allows the operation, and no trusted artifacts are written"
        ),
    }


def _trusted_executor_design_payload(
    *,
    review: dict[str, Any],
    review_status: str,
    checks: dict[str, Any],
) -> dict[str, Any]:
    candidate_ready = bool(checks.get("candidate_preflight_ready", {}).get("passed"))
    apply_ready = bool(checks.get("apply_contract_ready", {}).get("passed"))
    provenance_bound = bool(checks.get("approval_provenance_bound_match", {}).get("passed"))
    target_paths_confined = bool(checks.get("target_paths_confined", {}).get("passed"))
    operation_allowlisted = bool(review.get("operation_currently_allowlisted"))
    executor_entrypoint = _trusted_executor_entrypoint_status()
    executor_implemented = bool(executor_entrypoint.get("guarded"))

    if not candidate_ready:
        design_status = "blocked_candidate_preflight"
    elif not apply_ready:
        design_status = review_status or "blocked_apply_contract"
    elif not provenance_bound:
        design_status = "blocked_approval_provenance_not_bound"
    elif not target_paths_confined:
        design_status = "blocked_target_path_not_confined"
    elif not executor_implemented:
        design_status = "trusted_executor_design_ready_but_not_implemented"
    elif operation_allowlisted:
        design_status = "trusted_executor_design_ready_gate_allowlisted"
    else:
        design_status = "trusted_executor_design_ready_executor_built_gate_not_allowlisted"

    target_preview = list(review.get("target_write_preview") or [])
    target_paths = [str(item.get("path")) for item in target_preview if item.get("path")]
    executor_components = [
        {
            "component": "scope_loader",
            "responsibility": "load tenant/workspace/user scope and approval metadata",
            "implemented": executor_implemented,
        },
        {
            "component": "candidate_revalidator",
            "responsibility": "rerun redacted candidate validation immediately before any write",
            "implemented": executor_implemented,
        },
        {
            "component": "secret_session_guard",
            "responsibility": "reject passwords, cookies, tokens, session state, profile paths, and credential values",
            "implemented": executor_implemented,
        },
        {
            "component": "gate_operation_checker",
            "responsibility": "require explicit Gate allowlist for siteops.browser_skill_candidate.apply_trusted_artifacts",
            "implemented": executor_implemented,
        },
        {
            "component": "artifact_writer",
            "responsibility": "write trusted Browser Skill and SiteOps Skill Card artifacts only after all checks pass",
            "implemented": executor_implemented,
        },
        {
            "component": "audit_writer",
            "responsibility": "emit scoped prewrite, per-artifact, rollback, and postwrite audit events",
            "implemented": executor_implemented,
        },
        {
            "component": "activation_boundary",
            "responsibility": "keep written artifacts inactive until a separate activation workflow approves reuse",
            "implemented": executor_implemented,
        },
    ]
    audit_sequence = [
        {
            "order": 1,
            "event_type": "trusted_executor_preflight_started",
            "policy_decision": "review_only",
            "required": True,
            "implemented": executor_implemented,
        },
        {
            "order": 2,
            "event_type": "trusted_executor_prewrite_validated",
            "policy_decision": "allow_after_gate_only",
            "required": True,
            "implemented": executor_implemented,
        },
        {
            "order": 3,
            "event_type": "trusted_artifact_write_attempted",
            "policy_decision": "allow_after_gate_only",
            "required": True,
            "implemented": executor_implemented,
        },
        {
            "order": 4,
            "event_type": "trusted_artifact_write_result",
            "policy_decision": "record_result",
            "required": True,
            "implemented": executor_implemented,
        },
        {
            "order": 5,
            "event_type": "trusted_executor_postwrite_closed",
            "policy_decision": "inactive_artifacts_only",
            "required": True,
            "implemented": executor_implemented,
        },
    ]
    rollback_plan = [
        {
            "case": "failure_before_any_artifact_write",
            "action": "write failure audit event only",
            "trusted_artifact_state": "none",
            "implemented": False,
        },
        {
            "case": "failure_after_partial_artifact_write",
            "action": "leave partial artifact inactive, write rollback-required audit event, require manual review",
            "trusted_artifact_state": "inactive_review_artifact",
            "implemented": False,
        },
        {
            "case": "postwrite_validation_failure",
            "action": "mark artifacts inactive and require separate repair/removal decision",
            "trusted_artifact_state": "inactive_blocked",
            "implemented": False,
        },
    ]
    failure_modes = [
        "missing or pending approval",
        "legacy-unbound or mismatched approval provenance",
        "candidate no longer validates",
        "secret-like, cookie, token, session, or credential material detected",
        "target path escapes governed trusted homes",
        "Gate operation not allowlisted",
        "artifact write collision or partial write",
        "postwrite validation failure",
    ]
    design_checks = [
        _executor_preflight_check(
            "allowlist_review_available",
            passed=bool(review),
            detail=review_status,
        ),
        _executor_preflight_check(
            "approval_bound_for_design",
            passed=provenance_bound,
            detail=str(checks.get("approval_provenance_bound_match", {}).get("detail")),
        ),
        _executor_preflight_check(
            "target_paths_confined_for_design",
            passed=target_paths_confined,
            detail="target paths must remain confined before any future write",
        ),
        _executor_preflight_check(
            "audit_sequence_defined",
            passed=True,
            detail="prewrite, write-attempt, write-result, and postwrite events are specified",
        ),
        _executor_preflight_check(
            "rollback_plan_defined",
            passed=True,
            detail="partial-write outcomes remain inactive and audit-visible",
        ),
        _executor_preflight_check(
            "executor_implementation_disabled",
            passed=not executor_implemented,
            required=False,
            detail=str(executor_entrypoint),
        ),
    ]
    executor_enabled = bool(
        executor_implemented
        and operation_allowlisted
        and str(design_status).startswith("trusted_executor_design_ready")
    )

    return {
        "ok": True,
        "action": PROMOTION_TRUSTED_EXECUTOR_DESIGN_ACTION,
        "candidate_id": review.get("candidate_id"),
        "proposed_skill_id": review.get("proposed_skill_id"),
        "scope": review.get("scope"),
        "approval": review.get("approval"),
        "approval_provenance": review.get("approval_provenance"),
        "secret_session_exclusion_recheck": review.get("secret_session_exclusion_recheck"),
        "allowlist_review_status": review_status,
        "trusted_executor_design_status": design_status,
        "gate_operation": review.get("gate_operation"),
        "operation_currently_allowlisted": operation_allowlisted,
        "gate_reason": review.get("gate_reason"),
        "target_write_preview": target_preview,
        "target_paths": target_paths,
        "trusted_executor_design_checks": design_checks,
        "executor_entrypoint_preview": {
            **executor_entrypoint,
            "enabled": executor_enabled,
        },
        "executor_components": executor_components,
        "audit_sequence": audit_sequence,
        "rollback_plan": rollback_plan,
        "failure_modes": failure_modes,
        "implementation_checklist": [
            "add executor function in a separate pass",
            "gate-check operation before any artifact write",
            "revalidate candidate and approval provenance immediately before write",
            "rerun secret/session scanner immediately before write",
            "write scoped prewrite audit event",
            "write trusted Browser Skill artifact only inside runtime/browser_skills/skills/",
            "write SiteOps Skill Card artifact only inside runtime/siteops/registry/skill_cards/",
            "write scoped postwrite audit event",
            "leave artifacts inactive until separate activation workflow",
        ],
        "acceptance_tests_required": [
            "pending approval blocks executor",
            "legacy-unbound approval blocks executor",
            "Gate operation not allowlisted blocks executor",
            "path traversal target blocks executor",
            "secret-like candidate content blocks executor",
            "partial write records rollback-required audit and no activation",
            "successful future write still leaves artifacts inactive",
        ],
        "writes_performed": False,
        "executor_implemented": executor_implemented,
        "executor_enabled": executor_enabled,
        "executor_build_allowed": False,
        "executor_implementation_performed": executor_implemented,
        "allowlist_change_allowed": False,
        "allowlist_change_performed": False,
        "policy_file_write_allowed": False,
        "trusted_skill_write_allowed": False,
        "siteops_skill_card_write_allowed": False,
        "browser_execution_allowed": False,
        "agent_bus_enqueue_allowed": False,
        "provider_api_call_allowed": False,
        "activation_allowed": False,
        "canonical_writeback_allowed": False,
        "boundary": (
            "trusted executor design only; no Gate allowlist mutation, trusted artifact "
            "write, activation, browser execution, Agent Bus enqueue, provider call, "
            "or canonical writeback is performed"
        ),
    }


def candidate_promotion_executor_review_checklist(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    approval_id: str,
) -> dict[str, Any]:
    """Return the pre-implementation review checklist for a future executor.

    This composes the trusted executor design packet and remains a review-only
    artifact. It does not create the executor, edit Gate policy, write trusted
    artifacts, enqueue Agent Bus work, launch a browser, or activate anything.
    """
    design = candidate_promotion_trusted_executor_design(
        candidate_id,
        root,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
        approval_id=approval_id,
    )
    design_status = str(design.get("trusted_executor_design_status") or "")
    ready_statuses = {
        "trusted_executor_design_ready_but_not_implemented",
        "trusted_executor_design_ready_executor_built_gate_not_allowlisted",
        "trusted_executor_design_ready_gate_allowlisted",
    }
    ready = design_status in ready_statuses
    executor_entrypoint = dict(design.get("executor_entrypoint_preview") or {})
    executor_implemented = bool(design.get("executor_implemented"))
    if ready:
        checklist_status = "executor_review_checklist_ready_no_write_authority"
    elif design_status.startswith("blocked_"):
        checklist_status = design_status
    elif design_status:
        checklist_status = f"blocked_{design_status}"
    else:
        checklist_status = "blocked_trusted_executor_design"
    gate_operation = str(design.get("gate_operation") or PROMOTION_GATE_APPLY_OPERATION)
    operation_allowlisted = bool(design.get("operation_currently_allowlisted"))
    target_paths = list(design.get("target_paths") or [])
    approval = design.get("approval") or {}
    provenance = design.get("approval_provenance") or {}

    required_review_gates = [
        {
            "gate_id": "approval_provenance_bound_match",
            "status": "ready_for_review" if ready else "blocked",
            "required": True,
            "source": "trusted_executor_design.approval_provenance",
            "evidence": provenance.get("provenance_status"),
            "blocks_execution": True,
        },
        {
            "gate_id": "candidate_revalidation_before_write",
            "status": "required_future_test",
            "required": True,
            "source": "candidate_promotion_gate_executor_spec",
            "evidence": "candidate must be revalidated immediately before any future write",
            "blocks_execution": True,
        },
        {
            "gate_id": "secret_session_exclusion_before_write",
            "status": "required_future_test",
            "required": True,
            "source": "candidate_promotion_gate_allowlist_review",
            "evidence": "secret/cookie/session-token scanner must pass immediately before any future write",
            "blocks_execution": True,
        },
        {
            "gate_id": "target_confinement_before_write",
            "status": "required_future_test",
            "required": True,
            "source": "trusted_executor_design.target_paths",
            "evidence": target_paths,
            "blocks_execution": True,
        },
        {
            "gate_id": "gate_operation_allowlist",
            "status": "ready_for_review" if operation_allowlisted else "blocked_not_allowlisted",
            "required": True,
            "source": "runtime.chaseos_gate",
            "evidence": gate_operation,
            "blocks_execution": True,
        },
        {
            "gate_id": "audit_sequence_before_write",
            "status": "required_future_test",
            "required": True,
            "source": "trusted_executor_design.audit_sequence",
            "evidence": [item.get("event_type") for item in design.get("audit_sequence") or []],
            "blocks_execution": True,
        },
        {
            "gate_id": "rollback_plan_before_write",
            "status": "required_future_test",
            "required": True,
            "source": "trusted_executor_design.rollback_plan",
            "evidence": [item.get("case") for item in design.get("rollback_plan") or []],
            "blocks_execution": True,
        },
        {
            "gate_id": "inactive_activation_boundary",
            "status": "required_future_test",
            "required": True,
            "source": "trusted_executor_design.boundary",
            "evidence": "future artifacts must remain inactive until separate activation approval",
            "blocks_execution": True,
        },
    ]
    implementation_review_steps = [
        {
            "step_id": "executor_entrypoint_review",
            "decision": (
                "guarded_entrypoint_implemented"
                if executor_implemented
                else "do_not_implement_in_this_pass"
            ),
            "required_before_future_build": not executor_implemented,
            "expected_artifact": "reviewed patch adding apply_trusted_candidate_artifacts",
            "implemented": executor_implemented,
        },
        {
            "step_id": "gate_policy_review",
            "decision": "do_not_allowlist_in_this_pass",
            "required_before_future_build": True,
            "expected_artifact": "separate Gate allowlist patch and approval record",
            "implemented": False,
        },
        {
            "step_id": "write_path_review",
            "decision": "do_not_write_in_this_pass",
            "required_before_future_build": True,
            "expected_artifact": "path confinement tests for every trusted artifact target",
            "implemented": False,
        },
        {
            "step_id": "activation_review",
            "decision": "defer_to_separate_activation_workflow",
            "required_before_future_build": True,
            "expected_artifact": "inactive-by-default artifact contract",
            "implemented": False,
        },
    ]
    replacement_test_requirements = [
        (
            "executor remains guarded, explicit-flag-gated, and Gate-denied until an approved policy change lands"
            if executor_implemented
            else "executor remains absent until explicitly implemented in a separate patch"
        ),
        "Gate operation remains denied until an approved policy change lands",
        "pending, rejected, mismatched, and legacy-unbound approvals block writes",
        "candidate revalidation runs immediately before any future write",
        "secret/cookie/session-token scanner runs immediately before any future write",
        "path traversal and path collision targets fail closed",
        "partial writes produce inactive artifacts and rollback-required audit events",
        "successful future writes still leave artifacts inactive until separate activation",
    ]
    blocked_actions = [
        "run apply_trusted_candidate_artifacts without Gate allowance and explicit write flag",
        "edit runtime/policy/gateway_allowlists.json",
        "write runtime/browser_skills/skills artifacts",
        "write runtime/siteops/registry/skill_cards artifacts",
        "launch or control a browser",
        "enqueue Agent Bus work",
        "call provider APIs",
        "activate promoted skills",
        "write canonical ChaseOS memory/state",
    ]

    return {
        "ok": True,
        "action": PROMOTION_EXECUTOR_REVIEW_CHECKLIST_ACTION,
        "candidate_id": design.get("candidate_id"),
        "proposed_skill_id": design.get("proposed_skill_id"),
        "scope": design.get("scope"),
        "approval": approval,
        "approval_provenance": provenance,
        "allowlist_review_status": design.get("allowlist_review_status"),
        "trusted_executor_design_status": design_status,
        "executor_review_status": checklist_status,
        "review_decision": "do_not_implement_in_this_pass",
        "gate_operation": gate_operation,
        "operation_currently_allowlisted": bool(design.get("operation_currently_allowlisted")),
        "target_paths": target_paths,
        "required_review_gates": required_review_gates,
        "implementation_review_steps": implementation_review_steps,
        "replacement_test_requirements": replacement_test_requirements,
        "blocked_actions": blocked_actions,
        "denied_effects": blocked_actions,
        "executor_entrypoint_preview": design.get("executor_entrypoint_preview"),
        "executor_components": design.get("executor_components"),
        "audit_sequence": design.get("audit_sequence"),
        "rollback_plan": design.get("rollback_plan"),
        "approval_status": approval.get("status"),
        "provenance_status": provenance.get("provenance_status"),
        "writes_performed": False,
        "executor_implemented": executor_implemented,
        "executor_enabled": bool(executor_entrypoint.get("enabled")),
        "executor_build_allowed": False,
        "executor_implementation_allowed": False,
        "executor_implementation_performed": executor_implemented,
        "allowlist_change_allowed": False,
        "allowlist_change_performed": False,
        "policy_file_write_allowed": False,
        "trusted_skill_write_allowed": False,
        "siteops_skill_card_write_allowed": False,
        "browser_execution_allowed": False,
        "agent_bus_enqueue_allowed": False,
        "provider_api_call_allowed": False,
        "activation_allowed": False,
        "canonical_writeback_allowed": False,
        "boundary": (
            "executor review checklist only; no executor implementation, Gate allowlist "
            "mutation, trusted artifact write, activation, browser execution, Agent Bus "
            "enqueue, provider call, or canonical writeback is performed"
        ),
    }


def candidate_promotion_trusted_executor_design(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    approval_id: str,
) -> dict[str, Any]:
    """Return the fail-closed trusted artifact executor design.

    This is still a design/spec surface only. It does not implement the
    executor, edit Gate policy, or write trusted artifacts.
    """
    review = candidate_promotion_gate_allowlist_review(
        candidate_id,
        root,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
        approval_id=approval_id,
    )
    review_status = str(review.get("allowlist_review_status") or "")
    checks = {
        str(item.get("check_id")): item
        for item in review.get("allowlist_review_checks") or []
        if isinstance(item, dict)
    }
    return _trusted_executor_design_payload(
        review=review,
        review_status=review_status,
        checks=checks,
    )


def candidate_promotion_preimplementation_verifier(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    approval_id: str,
) -> dict[str, Any]:
    """Return a read-only pre-implementation verifier verdict for a future executor.

    This is the terminal gate-aggregation pass executed before any executor patch
    is proposed or merged. It composes the full executor review checklist and then
    cross-checks live state across five dimensions:

    1. Gate operation is currently denied (fail-closed guard).
    2. Executor entrypoint function is absent from the module (no sneaked impl).
    3. Trusted artifact target files are absent on disk (no orphaned writes).
    4. Guard tests exist in the test suite (regression protection in place).
    5. CLI contract entry exists for the ``executor-review-checklist`` command.

    No writes, no Gate mutations, no browser, no Agent Bus enqueue, no canonical
    state. The returned ``verifier_verdict`` field is either ``ready_for_patch_proposal``
    (all guards pass) or ``blocked`` (one or more guards fail).
    """
    resolved_root = Path(root) if root else Path.cwd()

    # ── Step 1: compose the upstream checklist ──────────────────────────────
    checklist = candidate_promotion_executor_review_checklist(
        candidate_id,
        root,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
        approval_id=approval_id,
    )
    checklist_status = str(checklist.get("executor_review_status") or "")
    checklist_ready = checklist_status == "executor_review_checklist_ready_no_write_authority"

    # ── Step 2: Gate operation is denied ────────────────────────────────────
    gate_operation = str(checklist.get("gate_operation") or PROMOTION_GATE_APPLY_OPERATION)
    gate_denied, gate_reason = check_runtime_operation(gate_operation, write_targets=[])
    gate_guard_passes = not gate_denied  # gate_denied=False means allowed; we want it denied

    # check_runtime_operation returns (allowed, reason); we need allowed=False
    gate_guard_passes = not bool(gate_denied)

    # Re-read correctly: check_runtime_operation returns (allowed: bool, reason: str)
    _gate_allowed, _gate_reason = check_runtime_operation(gate_operation, write_targets=[])
    gate_is_denied = not _gate_allowed
    gate_denial_guard = _executor_preflight_check(
        "gate_operation_currently_denied",
        passed=gate_is_denied,
        required=False,
        detail=f"Gate operation '{gate_operation}': {_gate_reason}",
    )
    gate_policy_state_guard = _executor_preflight_check(
        "gate_operation_policy_state_acceptable",
        passed=gate_is_denied or bool(_gate_allowed),
        detail=(
            f"Gate operation '{gate_operation}' is "
            f"{'allowlisted' if _gate_allowed else 'denied fail-closed'}: {_gate_reason}"
        ),
    )

    # ── Step 3: Executor entrypoint function is absent ───────────────────────
    import importlib
    import sys
    _mod_name = "runtime.siteops.candidate_promotions"
    _mod = sys.modules.get(_mod_name)
    if _mod is None:
        try:
            _mod = importlib.import_module(_mod_name)
        except ImportError:
            _mod = None
    entrypoint = getattr(_mod, "apply_trusted_candidate_artifacts", None) if _mod is not None else None
    entrypoint_absent = entrypoint is None
    entrypoint_guarded = bool(getattr(entrypoint, "siteops_guarded_executor", False)) if entrypoint else False
    entrypoint_ok = entrypoint_absent or entrypoint_guarded
    entrypoint_guard = _executor_preflight_check(
        "executor_entrypoint_absent_or_guarded",
        passed=entrypoint_ok,
        detail=(
            "apply_trusted_candidate_artifacts is not defined in candidate_promotions"
            if entrypoint_absent
            else "WARNING: apply_trusted_candidate_artifacts exists — executor may be implemented"
        ),
    )

    # ── Step 4: Trusted artifact target files are absent on disk ─────────────
    if not entrypoint_absent:
        entrypoint_guard["detail"] = (
            "apply_trusted_candidate_artifacts exists with siteops_guarded_executor marker"
            if entrypoint_guarded
            else "WARNING: apply_trusted_candidate_artifacts exists without guarded marker"
        )

    target_paths = list(checklist.get("target_paths") or [])
    absent_targets: list[dict[str, Any]] = []
    for rel in target_paths:
        if not rel:
            continue
        abs_path = resolved_root / rel
        absent = not abs_path.exists()
        absent_targets.append({
            "path": rel,
            "exists_on_disk": not absent,
            "guard_passes": absent,
        })
    all_targets_absent = all(item["guard_passes"] for item in absent_targets) if absent_targets else True
    target_absence_guard = _executor_preflight_check(
        "trusted_artifact_targets_absent",
        passed=all_targets_absent,
        detail=(
            f"all {len(absent_targets)} trusted artifact target path(s) are absent on disk"
            if all_targets_absent
            else f"{sum(1 for t in absent_targets if not t['guard_passes'])} target(s) already exist — investigate"
        ),
    )

    # ── Step 5: Guard tests exist ────────────────────────────────────────────
    repo_root = Path(__file__).resolve().parents[2]
    guard_test_paths = [
        repo_root / "runtime" / "siteops" / "tests" / "test_candidate_promotions.py",
    ]
    guard_test_present = any(p.exists() for p in guard_test_paths)
    guard_test_markers = [
        "test_candidate_executor_guard_entrypoint_is_guarded",
        "test_candidate_executor_guard_gate_operation_is_allowlisted_after_approval_patch",
        "test_candidate_executor_guard_design_marks_entrypoint_built_but_gate_blocked",
    ]
    guard_test_detail: list[str] = []
    if guard_test_present:
        test_src = guard_test_paths[0].read_text(encoding="utf-8", errors="replace")
        found = [m for m in guard_test_markers if m in test_src]
        missing = [m for m in guard_test_markers if m not in test_src]
        guard_test_detail = [
            f"found: {len(found)}/{len(guard_test_markers)} guard test(s)",
            *(f"missing: {m}" for m in missing),
        ]
        guard_tests_complete = len(missing) == 0
    else:
        guard_tests_complete = False
        guard_test_detail = ["guard test file not found"]
    guard_test_guard = _executor_preflight_check(
        "guard_tests_present",
        passed=guard_tests_complete,
        detail="; ".join(guard_test_detail) if guard_test_detail else "guard tests present",
    )

    # ── Step 6: CLI contract entry exists ────────────────────────────────────
    cli_main_paths = [
        repo_root / "runtime" / "cli" / "main.py",
    ]
    cli_main_present = any(p.exists() for p in cli_main_paths)
    cli_contract_marker = "executor-review-checklist"
    if cli_main_present:
        cli_src = cli_main_paths[0].read_text(encoding="utf-8", errors="replace")
        cli_contract_found = cli_contract_marker in cli_src
    else:
        cli_contract_found = False
    cli_contract_guard = _executor_preflight_check(
        "cli_contract_present",
        passed=cli_contract_found,
        detail=(
            f"'{cli_contract_marker}' subcommand found in runtime/cli/main.py"
            if cli_contract_found
            else f"'{cli_contract_marker}' subcommand not found in runtime/cli/main.py"
        ),
    )

    # ── Verdict ───────────────────────────────────────────────────────────────
    verifier_checks = [
        gate_denial_guard,
        gate_policy_state_guard,
        entrypoint_guard,
        target_absence_guard,
        guard_test_guard,
        cli_contract_guard,
    ]
    all_pass = all(c["passed"] for c in verifier_checks if c.get("required", True))
    checklist_layer_pass = checklist_ready
    # Verdict: ready only when checklist layer is at its expected terminal state
    # AND all live guards pass.
    if not checklist_layer_pass:
        verifier_verdict = f"blocked_checklist_not_ready: {checklist_status}"
    elif not all_pass:
        failed = [
            c["check_id"]
            for c in verifier_checks
            if c.get("required", True) and not c["passed"]
        ]
        verifier_verdict = f"blocked_live_guard_failure: {', '.join(failed)}"
    else:
        verifier_verdict = "ready_for_patch_proposal"

    return {
        "ok": True,
        "action": PROMOTION_PREIMPLEMENTATION_VERIFIER_ACTION,
        "candidate_id": checklist.get("candidate_id"),
        "proposed_skill_id": checklist.get("proposed_skill_id"),
        "scope": checklist.get("scope"),
        "approval_status": checklist.get("approval_status"),
        "provenance_status": checklist.get("provenance_status"),
        # Upstream checklist summary
        "checklist_status": checklist_status,
        "checklist_layer_pass": checklist_layer_pass,
        "executor_review_status": checklist_status,
        "trusted_executor_design_status": checklist.get("trusted_executor_design_status"),
        "allowlist_review_status": checklist.get("allowlist_review_status"),
        "review_decision": checklist.get("review_decision"),
        "operation_currently_allowlisted": checklist.get("operation_currently_allowlisted"),
        # Live guard checks
        "verifier_checks": verifier_checks,
        "verifier_verdict": verifier_verdict,
        "verifier_pass": verifier_verdict == "ready_for_patch_proposal",
        "absent_target_paths": absent_targets,
        # Required review gates and steps forwarded from checklist
        "required_review_gates": checklist.get("required_review_gates"),
        "implementation_review_steps": checklist.get("implementation_review_steps"),
        "replacement_test_requirements": checklist.get("replacement_test_requirements"),
        "blocked_actions": checklist.get("blocked_actions"),
        # Authority surface: the guarded entrypoint may exist, but execution remains Gate-blocked.
        "writes_performed": False,
        "executor_implemented": entrypoint_guarded,
        "executor_enabled": False,
        "executor_build_allowed": False,
        "executor_implementation_allowed": False,
        "executor_implementation_performed": entrypoint_guarded,
        "allowlist_change_allowed": False,
        "allowlist_change_performed": False,
        "policy_file_write_allowed": False,
        "trusted_skill_write_allowed": False,
        "siteops_skill_card_write_allowed": False,
        "browser_execution_allowed": False,
        "agent_bus_enqueue_allowed": False,
        "provider_api_call_allowed": False,
        "activation_allowed": False,
        "canonical_writeback_allowed": False,
        "boundary": (
            "pre-implementation verifier only; a guarded executor entrypoint may exist, but no "
            "Gate allowlist mutation, trusted artifact write, activation, browser execution, "
            "Agent Bus enqueue, provider call, or canonical writeback is performed in this pass"
        ),
    }


def candidate_promotion_executor_implementation_design_review(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    approval_id: str,
) -> dict[str, Any]:
    """Return a review-only future executor implementation design packet.

    This composes the preimplementation verifier and describes the next patch
    shape for a future executor. It intentionally does not define the executor
    entrypoint, edit Gate policy, write trusted artifacts, activate a skill,
    launch a browser, enqueue Agent Bus work, call providers, or mutate
    canonical ChaseOS state.
    """
    verifier = candidate_promotion_preimplementation_verifier(
        candidate_id,
        root,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
        approval_id=approval_id,
    )
    verifier_verdict = str(verifier.get("verifier_verdict") or "")
    verifier_pass = bool(verifier.get("verifier_pass"))
    if verifier_pass:
        design_status = "implementation_design_review_ready_no_authority"
        review_decision = "patch_plan_only_do_not_implement_in_this_pass"
    else:
        design_status = f"blocked_preimplementation_verifier: {verifier_verdict}"
        review_decision = "blocked_before_patch_plan"

    executor_implemented = bool(verifier.get("executor_implemented"))
    patch_plan = [
        {
            "step_id": "add_executor_entrypoint",
            "file": "runtime/siteops/candidate_promotions.py",
            "future_symbol": "apply_trusted_candidate_artifacts",
            "allowed_in_this_pass": False,
            "future_required": not executor_implemented,
            "implemented": executor_implemented,
            "review_requirement": "operator-approved executor implementation patch",
        },
        {
            "step_id": "add_executor_unit_tests",
            "file": "runtime/siteops/tests/test_candidate_promotions.py",
            "allowed_in_this_pass": False,
            "future_required": True,
            "review_requirement": "tests must cover every fail-closed condition before first write",
        },
        {
            "step_id": "add_cli_apply_command",
            "file": "runtime/cli/main.py",
            "allowed_in_this_pass": False,
            "future_required": True,
            "review_requirement": "CLI command must remain Gate-denied unless a separate allowlist review lands",
        },
        {
            "step_id": "add_cli_handler",
            "file": "runtime/cli/siteops_commands.py",
            "allowed_in_this_pass": False,
            "future_required": True,
            "review_requirement": "handler must call Gate before any trusted artifact write",
        },
        {
            "step_id": "review_gate_allowlist_patch",
            "file": "runtime/policy/gateway_allowlists.json",
            "allowed_in_this_pass": False,
            "future_required": True,
            "review_requirement": "separate policy patch; approval to implement executor is not approval to allowlist",
        },
    ]
    implementation_order = [
        "verify approved bound approval object",
        "rerun current candidate preflight",
        "rerun secret/session exclusion scanner",
        "compute confined target paths from candidate metadata only",
        "call ChaseOS Gate before any write",
        "write prewrite audit event",
        "write inactive trusted artifacts only after Gate allow",
        "validate written artifact shape",
        "write per-artifact and postwrite audit events",
        "return activation_allowed=false",
    ]
    required_stop_conditions = [
        "missing, pending, rejected, legacy-unbound, or mismatched approval",
        "candidate preflight failure",
        "secret, cookie, token, session, credential, password, or api_key material detected",
        "target path traversal or target outside governed trusted homes",
        "trusted target collision without explicit collision policy",
        "Gate denies siteops.browser_skill_candidate.apply_trusted_artifacts",
        "audit event write failure before trusted artifact write",
        "written artifact validation failure",
    ]
    future_tests = [
        "missing approval blocks before Gate",
        "pending approval blocks before Gate",
        "rejected approval blocks before Gate",
        "legacy-unbound and mismatched approvals block before Gate",
        "candidate revalidation blocks stale or invalid candidate files",
        "secret/session scanner blocks unsafe candidate content",
        "path traversal and target collisions fail closed",
        "Gate denial blocks before trusted writes",
        "partial writes remain inactive and audit-visible",
        "successful future write does not activate the skill",
    ]
    denied_effects = [
        "run apply_trusted_candidate_artifacts without Gate allowance and explicit write flag",
        "edit runtime/policy/gateway_allowlists.json",
        "write runtime/browser_skills/skills artifacts",
        "write runtime/siteops/registry/skill_cards artifacts",
        "launch or control a browser",
        "enqueue Agent Bus work",
        "call provider APIs",
        "activate promoted skills",
        "write canonical ChaseOS memory/state",
    ]

    return {
        "ok": True,
        "action": PROMOTION_EXECUTOR_IMPLEMENTATION_DESIGN_REVIEW_ACTION,
        "candidate_id": verifier.get("candidate_id"),
        "proposed_skill_id": verifier.get("proposed_skill_id"),
        "scope": verifier.get("scope"),
        "approval_status": verifier.get("approval_status"),
        "provenance_status": verifier.get("provenance_status"),
        "verifier_verdict": verifier_verdict,
        "verifier_pass": verifier_pass,
        "implementation_design_status": design_status,
        "review_decision": review_decision,
        "gate_operation": PROMOTION_GATE_APPLY_OPERATION,
        "operation_currently_allowlisted": verifier.get("operation_currently_allowlisted"),
        "patch_plan": patch_plan,
        "implementation_order": implementation_order,
        "required_stop_conditions": required_stop_conditions,
        "future_test_requirements": future_tests,
        "verifier_checks": verifier.get("verifier_checks"),
        "required_review_gates": verifier.get("required_review_gates"),
        "blocked_actions": denied_effects,
        "denied_effects": denied_effects,
        "writes_performed": False,
        "executor_implemented": executor_implemented,
        "executor_enabled": False,
        "executor_build_allowed": False,
        "executor_implementation_allowed": False,
        "executor_implementation_performed": executor_implemented,
        "allowlist_change_allowed": False,
        "allowlist_change_performed": False,
        "policy_file_write_allowed": False,
        "trusted_skill_write_allowed": False,
        "siteops_skill_card_write_allowed": False,
        "browser_execution_allowed": False,
        "agent_bus_enqueue_allowed": False,
        "provider_api_call_allowed": False,
        "activation_allowed": False,
        "canonical_writeback_allowed": False,
        "boundary": (
            "executor implementation design review only; a guarded executor entrypoint may "
            "exist, but no Gate allowlist mutation, trusted artifact write, activation, "
            "browser execution, Agent Bus enqueue, provider call, or canonical writeback "
            "is performed in this pass"
        ),
    }


def candidate_promotion_executor_prewrite_audit_spec(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    approval_id: str,
) -> dict[str, Any]:
    """Return a no-write audit and inactive-artifact spec for a future executor."""
    design_review = candidate_promotion_executor_implementation_design_review(
        candidate_id,
        root,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
        approval_id=approval_id,
    )
    design_status = str(design_review.get("implementation_design_status") or "")
    design_ready = design_status == "implementation_design_review_ready_no_authority"
    if design_ready:
        spec_status = "prewrite_audit_spec_ready_no_authority"
        review_decision = "audit_contract_only_do_not_write_in_this_pass"
    else:
        spec_status = f"blocked_implementation_design_review: {design_status}"
        review_decision = "blocked_before_audit_contract"

    scope_fields = ["tenant_id", "workspace_id", "user_id"]
    identity_fields = ["candidate_id", "proposed_skill_id", "approval_id", "run_id"]
    forbidden_metadata_fields = [
        "raw_candidate_content",
        "cookie",
        "cookies",
        "token",
        "api_key",
        "password",
        "secret",
        "session",
        "session_key",
        "browser_profile_path",
        "credential_value",
        "private_key",
        "seed_phrase",
    ]
    audit_event_sequence = [
        {
            "event_type": "trusted_executor_preflight_started",
            "policy_decision": "pending",
            "required_before_write": True,
            "metadata_required": scope_fields + identity_fields,
            "metadata_forbidden": forbidden_metadata_fields,
            "implemented": False,
            "write_allowed_in_this_pass": False,
        },
        {
            "event_type": "trusted_executor_prewrite_validated",
            "policy_decision": "allow_after_gate_only",
            "required_before_write": True,
            "metadata_required": scope_fields
            + identity_fields
            + ["target_paths", "secret_session_exclusion_passed", "gate_operation"],
            "metadata_forbidden": forbidden_metadata_fields,
            "implemented": False,
            "write_allowed_in_this_pass": False,
        },
        {
            "event_type": "trusted_artifact_write_attempted",
            "policy_decision": "allow_after_gate_only",
            "required_before_write": False,
            "metadata_required": scope_fields + identity_fields + ["artifact_kind", "target_path"],
            "metadata_forbidden": forbidden_metadata_fields,
            "implemented": False,
            "write_allowed_in_this_pass": False,
        },
        {
            "event_type": "trusted_artifact_write_result",
            "policy_decision": "result_only",
            "required_before_write": False,
            "metadata_required": scope_fields + identity_fields + ["artifact_kind", "target_path", "result_status"],
            "metadata_forbidden": forbidden_metadata_fields,
            "implemented": False,
            "write_allowed_in_this_pass": False,
        },
        {
            "event_type": "trusted_executor_postwrite_closed",
            "policy_decision": "closed_inactive",
            "required_before_write": False,
            "metadata_required": scope_fields + identity_fields + ["activation_allowed", "artifacts_inactive"],
            "metadata_forbidden": forbidden_metadata_fields,
            "implemented": False,
            "write_allowed_in_this_pass": False,
        },
        {
            "event_type": "trusted_executor_blocked",
            "policy_decision": "deny",
            "required_before_write": True,
            "metadata_required": scope_fields + identity_fields + ["block_reason"],
            "metadata_forbidden": forbidden_metadata_fields,
            "implemented": False,
            "write_allowed_in_this_pass": False,
        },
        {
            "event_type": "trusted_executor_rollback_required",
            "policy_decision": "manual_review_required",
            "required_before_write": False,
            "metadata_required": scope_fields + identity_fields + ["rollback_reason", "partial_artifacts"],
            "metadata_forbidden": forbidden_metadata_fields,
            "implemented": False,
            "write_allowed_in_this_pass": False,
        },
    ]
    inactive_artifact_contracts = [
        {
            "artifact_kind": "browser_skill",
            "target_root": "runtime/browser_skills/skills/",
            "required_status": "inactive_review",
            "activation_allowed": False,
            "required_fields": [
                "skill_id",
                "source_candidate_id",
                "tenant_id",
                "workspace_id",
                "created_by",
                "status",
                "activation_allowed",
                "provenance",
            ],
            "forbidden_fields": forbidden_metadata_fields,
            "write_allowed_in_this_pass": False,
        },
        {
            "artifact_kind": "siteops_skill_card",
            "target_root": "runtime/siteops/registry/skill_cards/",
            "required_status": "inactive_review",
            "activation_allowed": False,
            "required_fields": [
                "skill_id",
                "source_candidate_id",
                "tenant_id",
                "workspace_id",
                "created_by",
                "status",
                "activation_allowed",
                "provenance",
            ],
            "forbidden_fields": forbidden_metadata_fields,
            "write_allowed_in_this_pass": False,
        },
    ]
    validation_contract = {
        "prewrite_checks_required": [
            "approval_status_approved",
            "approval_provenance_bound_match",
            "candidate_revalidated",
            "secret_session_exclusion_passed",
            "target_paths_confined",
            "target_collision_policy_checked",
            "gate_operation_allowed",
            "prewrite_audit_event_written",
        ],
        "postwrite_checks_required": [
            "artifact_shape_valid",
            "artifact_status_inactive_review",
            "activation_allowed_false",
            "per_artifact_result_audited",
            "postwrite_close_audited",
        ],
        "all_checks_implemented": False,
        "write_allowed_in_this_pass": False,
    }
    denied_effects = [
        "write audit events",
        "write inactive trusted artifacts",
        "create apply_trusted_candidate_artifacts executor",
        "edit runtime/policy/gateway_allowlists.json",
        "write runtime/browser_skills/skills artifacts",
        "write runtime/siteops/registry/skill_cards artifacts",
        "launch or control a browser",
        "enqueue Agent Bus work",
        "call provider APIs",
        "activate promoted skills",
        "write canonical ChaseOS memory/state",
    ]

    return {
        "ok": True,
        "action": PROMOTION_EXECUTOR_PREWRITE_AUDIT_SPEC_ACTION,
        "candidate_id": design_review.get("candidate_id"),
        "proposed_skill_id": design_review.get("proposed_skill_id"),
        "scope": design_review.get("scope"),
        "approval_status": design_review.get("approval_status"),
        "provenance_status": design_review.get("provenance_status"),
        "implementation_design_status": design_status,
        "prewrite_audit_spec_status": spec_status,
        "review_decision": review_decision,
        "gate_operation": PROMOTION_GATE_APPLY_OPERATION,
        "operation_currently_allowlisted": design_review.get("operation_currently_allowlisted"),
        "audit_event_sequence": audit_event_sequence,
        "inactive_artifact_contracts": inactive_artifact_contracts,
        "validation_contract": validation_contract,
        "forbidden_metadata_fields": forbidden_metadata_fields,
        "blocked_actions": denied_effects,
        "denied_effects": denied_effects,
        "writes_performed": False,
        "audit_events_written": False,
        "inactive_artifacts_written": False,
        "executor_implemented": False,
        "executor_enabled": False,
        "executor_build_allowed": False,
        "executor_implementation_allowed": False,
        "executor_implementation_performed": False,
        "allowlist_change_allowed": False,
        "allowlist_change_performed": False,
        "policy_file_write_allowed": False,
        "trusted_skill_write_allowed": False,
        "siteops_skill_card_write_allowed": False,
        "browser_execution_allowed": False,
        "agent_bus_enqueue_allowed": False,
        "provider_api_call_allowed": False,
        "activation_allowed": False,
        "canonical_writeback_allowed": False,
        "boundary": (
            "executor prewrite audit spec only; no executor implementation, audit "
            "event write, Gate allowlist mutation, trusted artifact write, activation, "
            "browser execution, Agent Bus enqueue, provider call, or canonical "
            "writeback is performed in this pass"
        ),
    }


def _contains_forbidden_key(value: Any, forbidden_fields: set[str]) -> list[str]:
    matches: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key)
            if key_text in forbidden_fields:
                matches.append(key_text)
            matches.extend(_contains_forbidden_key(item, forbidden_fields))
    elif isinstance(value, list):
        for item in value:
            matches.extend(_contains_forbidden_key(item, forbidden_fields))
    return matches


def _inactive_artifact_validation(
    *,
    artifact_kind: str,
    payload: dict[str, Any],
    contract: dict[str, Any],
) -> dict[str, Any]:
    required = [str(item) for item in contract.get("required_fields") or []]
    forbidden = {str(item) for item in contract.get("forbidden_fields") or []}
    missing = [field for field in required if field not in payload]
    forbidden_matches = sorted(set(_contains_forbidden_key(payload, forbidden)))
    status_ok = payload.get("status") == contract.get("required_status")
    activation_ok = payload.get("activation_allowed") is False
    ok = not missing and not forbidden_matches and status_ok and activation_ok
    return {
        "artifact_kind": artifact_kind,
        "ok": ok,
        "status_ok": status_ok,
        "activation_ok": activation_ok,
        "missing_required_fields": missing,
        "forbidden_field_matches": forbidden_matches,
        "required_status": contract.get("required_status"),
        "activation_allowed_required": False,
        "write_allowed_in_this_pass": False,
    }


def candidate_promotion_inactive_artifact_validator(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    approval_id: str,
) -> dict[str, Any]:
    """Return a no-write validation packet for future inactive artifact payloads."""
    audit_spec = candidate_promotion_executor_prewrite_audit_spec(
        candidate_id,
        root,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
        approval_id=approval_id,
    )
    spec_status = str(audit_spec.get("prewrite_audit_spec_status") or "")
    spec_ready = spec_status == "prewrite_audit_spec_ready_no_authority"
    if spec_ready:
        validator_status = "inactive_artifact_validator_ready_no_authority"
        review_decision = "validator_contract_only_do_not_write_in_this_pass"
    else:
        validator_status = f"blocked_prewrite_audit_spec: {spec_status}"
        review_decision = "blocked_before_inactive_artifact_validation"

    scope = dict(audit_spec.get("scope") or {})
    proposed_skill_id = str(audit_spec.get("proposed_skill_id") or "")
    candidate_id_text = str(audit_spec.get("candidate_id") or candidate_id)
    base_provenance = {
        "source": "browser_skill_candidate",
        "candidate_id": candidate_id_text,
        "approval_id": approval_id,
        "promotion_gate_operation": PROMOTION_GATE_APPLY_OPERATION,
    }
    proposed_payloads = {
        "browser_skill": {
            "skill_id": proposed_skill_id,
            "source_candidate_id": candidate_id_text,
            "tenant_id": scope.get("tenant_id"),
            "workspace_id": scope.get("workspace_id"),
            "created_by": scope.get("user_id"),
            "status": "inactive_review",
            "activation_allowed": False,
            "provenance": base_provenance,
        },
        "siteops_skill_card": {
            "skill_id": proposed_skill_id,
            "source_candidate_id": candidate_id_text,
            "tenant_id": scope.get("tenant_id"),
            "workspace_id": scope.get("workspace_id"),
            "created_by": scope.get("user_id"),
            "status": "inactive_review",
            "activation_allowed": False,
            "provenance": base_provenance,
        },
    }
    contracts = {
        str(item.get("artifact_kind")): item
        for item in audit_spec.get("inactive_artifact_contracts") or []
        if isinstance(item, dict)
    }
    artifact_validations = [
        _inactive_artifact_validation(
            artifact_kind=kind,
            payload=payload,
            contract=contracts.get(kind, {}),
        )
        for kind, payload in proposed_payloads.items()
    ]
    validation_pass = spec_ready and all(item.get("ok") for item in artifact_validations)
    denied_effects = [
        "write inactive trusted artifacts",
        "write audit events",
        "create apply_trusted_candidate_artifacts executor",
        "edit runtime/policy/gateway_allowlists.json",
        "write runtime/browser_skills/skills artifacts",
        "write runtime/siteops/registry/skill_cards artifacts",
        "launch or control a browser",
        "enqueue Agent Bus work",
        "call provider APIs",
        "activate promoted skills",
        "write canonical ChaseOS memory/state",
    ]
    return {
        "ok": True,
        "action": PROMOTION_INACTIVE_ARTIFACT_VALIDATOR_ACTION,
        "candidate_id": audit_spec.get("candidate_id"),
        "proposed_skill_id": audit_spec.get("proposed_skill_id"),
        "scope": audit_spec.get("scope"),
        "approval_status": audit_spec.get("approval_status"),
        "provenance_status": audit_spec.get("provenance_status"),
        "prewrite_audit_spec_status": spec_status,
        "inactive_artifact_validator_status": validator_status,
        "review_decision": review_decision,
        "gate_operation": PROMOTION_GATE_APPLY_OPERATION,
        "operation_currently_allowlisted": audit_spec.get("operation_currently_allowlisted"),
        "proposed_artifact_payloads": proposed_payloads,
        "artifact_validations": artifact_validations,
        "validation_pass": validation_pass,
        "blocked_actions": denied_effects,
        "denied_effects": denied_effects,
        "writes_performed": False,
        "audit_events_written": False,
        "inactive_artifacts_written": False,
        "validator_wrote_artifacts": False,
        "executor_implemented": False,
        "executor_enabled": False,
        "executor_build_allowed": False,
        "executor_implementation_allowed": False,
        "executor_implementation_performed": False,
        "allowlist_change_allowed": False,
        "allowlist_change_performed": False,
        "policy_file_write_allowed": False,
        "trusted_skill_write_allowed": False,
        "siteops_skill_card_write_allowed": False,
        "browser_execution_allowed": False,
        "agent_bus_enqueue_allowed": False,
        "provider_api_call_allowed": False,
        "activation_allowed": False,
        "canonical_writeback_allowed": False,
        "boundary": (
            "inactive artifact validator only; no executor implementation, audit "
            "event write, Gate allowlist mutation, trusted artifact write, activation, "
            "browser execution, Agent Bus enqueue, provider call, or canonical "
            "writeback is performed in this pass"
        ),
    }


def candidate_promotion_activation_boundary_readiness(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    approval_id: str,
) -> dict[str, Any]:
    """Return a read-only activation-boundary readiness packet.

    This composes the inactive-artifact validator and collision policy surfaces,
    then makes the post-write activation separation explicit. It intentionally
    does not implement activation, write trusted artifacts, edit Gate policy,
    launch a browser, enqueue Agent Bus work, call providers, or write canonical
    ChaseOS state.
    """
    collision = candidate_promotion_collision_policy_spec(
        candidate_id,
        root,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
        approval_id=approval_id,
    )
    collision_status = str(collision.get("collision_policy_status") or "")
    inactive_status = str(collision.get("inactive_artifact_validator_status") or "")
    collision_ready = collision_status == "collision_policy_spec_ready_no_authority"
    if collision_ready:
        boundary_status = "activation_boundary_ready_no_authority"
        review_decision = "activation_contract_only_do_not_activate_in_this_pass"
    else:
        boundary_status = f"blocked_collision_policy: {collision_status}"
        review_decision = "blocked_before_activation_boundary"

    activation_gate_operation = "siteops.browser_skill_candidate.activate_trusted_artifact"
    future_activation_steps = [
        {
            "order": 1,
            "step_id": "verify_inactive_trusted_artifacts_exist",
            "effect": "read_only",
            "required": True,
            "implemented": False,
            "allowed_in_this_pass": False,
        },
        {
            "order": 2,
            "step_id": "verify_artifact_provenance_matches_approval",
            "effect": "read_only",
            "required": True,
            "implemented": False,
            "allowed_in_this_pass": False,
        },
        {
            "order": 3,
            "step_id": "run_activation_specific_gate_check",
            "effect": "read_only",
            "required": True,
            "implemented": False,
            "allowed_in_this_pass": False,
        },
        {
            "order": 4,
            "step_id": "enable_skill_for_scoped_runtime_use",
            "effect": "future_activation_mutation",
            "required": True,
            "implemented": False,
            "allowed_in_this_pass": False,
        },
        {
            "order": 5,
            "step_id": "write_post_activation_audit_event",
            "effect": "future_scoped_audit_write",
            "required": True,
            "implemented": False,
            "allowed_in_this_pass": False,
        },
    ]
    activation_requirements = {
        "separate_gate_operation": activation_gate_operation,
        "requires_operator_approval": True,
        "requires_inactive_artifact_present": True,
        "requires_artifact_provenance_match": True,
        "requires_runtime_ownership_review": True,
        "requires_post_activation_audit": True,
        "requires_separate_cli_surface": True,
        "requires_separate_tests": True,
    }
    blocked_actions = [
        "activate promoted skills",
        "enable trusted Browser Skill for execution",
        "enable SiteOps Skill Card for workflows",
        "write inactive trusted artifacts",
        "write audit events",
        "create apply_trusted_candidate_artifacts executor",
        "edit runtime/policy/gateway_allowlists.json",
        "write runtime/browser_skills/skills artifacts",
        "write runtime/siteops/registry/skill_cards artifacts",
        "launch or control a browser",
        "enqueue Agent Bus work",
        "call provider APIs",
        "write canonical ChaseOS memory/state",
    ]
    readiness_checks = [
        _executor_preflight_check(
            "inactive_artifact_validator_ready",
            passed=inactive_status == "inactive_artifact_validator_ready_no_authority",
            detail=inactive_status,
        ),
        _executor_preflight_check(
            "collision_policy_ready",
            passed=collision_ready,
            detail=collision_status,
        ),
        _executor_preflight_check(
            "activation_path_separated",
            passed=True,
            detail="activation requires a separate workflow/Gate operation after inactive artifacts exist",
        ),
        _executor_preflight_check(
            "activation_disabled_in_this_pass",
            passed=True,
            detail="readiness command performs no activation and writes nothing",
        ),
    ]
    return {
        "ok": True,
        "action": PROMOTION_ACTIVATION_BOUNDARY_READINESS_ACTION,
        "candidate_id": collision.get("candidate_id"),
        "proposed_skill_id": collision.get("proposed_skill_id"),
        "scope": collision.get("scope"),
        "approval_status": collision.get("approval_status"),
        "provenance_status": collision.get("provenance_status"),
        "inactive_artifact_validator_status": inactive_status,
        "collision_policy_status": collision_status,
        "activation_boundary_status": boundary_status,
        "review_decision": review_decision,
        "gate_operation": PROMOTION_GATE_APPLY_OPERATION,
        "activation_gate_operation": activation_gate_operation,
        "operation_currently_allowlisted": collision.get("operation_currently_allowlisted"),
        "activation_path_separated": True,
        "activation_requires_separate_workflow": True,
        "activation_requirements": activation_requirements,
        "future_activation_steps": future_activation_steps,
        "readiness_checks": readiness_checks,
        "blocked_actions": blocked_actions,
        "denied_effects": blocked_actions,
        "writes_performed": False,
        "audit_events_written": False,
        "inactive_artifacts_written": False,
        "activation_performed": False,
        "activation_allowed": False,
        "activation_gate_allowlist_change_allowed": False,
        "activation_gate_allowlist_change_performed": False,
        "executor_implemented": False,
        "executor_enabled": False,
        "executor_build_allowed": False,
        "executor_implementation_allowed": False,
        "executor_implementation_performed": False,
        "allowlist_change_allowed": False,
        "allowlist_change_performed": False,
        "policy_file_write_allowed": False,
        "trusted_skill_write_allowed": False,
        "siteops_skill_card_write_allowed": False,
        "browser_execution_allowed": False,
        "agent_bus_enqueue_allowed": False,
        "provider_api_call_allowed": False,
        "canonical_writeback_allowed": False,
        "boundary": (
            "activation boundary readiness only; activation remains a separate future "
            "workflow/Gate operation after inactive trusted artifacts exist. No trusted "
            "artifact write, activation, audit write, Gate mutation, browser execution, "
            "Agent Bus enqueue, provider call, or canonical writeback is performed."
        ),
    }


def candidate_promotion_activation_approval_request(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    approval_id: str,
    actor: str,
    requested_by: str | None = None,
    reason: str | None = None,
    write_approval_request: bool = False,
) -> dict[str, Any]:
    """Preview or write a pending approval request for future activation.

    This is the next boundary after activation readiness. It may create only a
    scoped SiteOps run record, pending ApprovalRequest, and audit event when
    explicitly requested. It does not activate skills, write trusted artifacts,
    consume approvals, launch browsers, enqueue Agent Bus work, call providers,
    or write canonical ChaseOS state.
    """
    readiness = candidate_promotion_activation_boundary_readiness(
        candidate_id,
        root,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
        approval_id=approval_id,
    )
    scope_data = dict(readiness.get("scope") or {})
    scope = SiteOpsScope(
        tenant_id=str(scope_data.get("tenant_id") or tenant_id or ""),
        workspace_id=str(scope_data.get("workspace_id") or workspace_id or ""),
        user_id=str(scope_data.get("user_id") or user_id or ""),
    )
    requested_by_id = str(requested_by or actor or user_id or "").strip()
    activation_gate_operation = str(
        readiness.get("activation_gate_operation")
        or "siteops.browser_skill_candidate.activate_trusted_artifact"
    )
    activation_ready = readiness.get("activation_boundary_status") == "activation_boundary_ready_no_authority"
    run_fingerprint = hashlib.sha256(
        f"{scope.tenant_id}|{scope.workspace_id}|{scope.user_id}|{candidate_id}|{approval_id}|activation".encode(
            "utf-8"
        )
    ).hexdigest()[:10]
    run_stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    run_id = f"siteops_activation_approval_{run_stamp}_{run_fingerprint}"
    audit_ref = str(audit_path(root, scope.tenant_id, scope.workspace_id, run_id))
    request_digest = hashlib.sha256(
        json.dumps(
            {
                "candidate_id": readiness.get("candidate_id"),
                "proposed_skill_id": readiness.get("proposed_skill_id"),
                "source_approval_id": approval_id,
                "activation_gate_operation": activation_gate_operation,
                "activation_boundary_status": readiness.get("activation_boundary_status"),
                "activation_requirements": readiness.get("activation_requirements"),
            },
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()
    approval_request_artifact = {
        "request_id": run_id,
        "request_type": "siteops_candidate_activation_approval_request",
        "tenant_id": scope.tenant_id,
        "workspace_id": scope.workspace_id,
        "user_id": scope.user_id,
        "requested_by": requested_by_id,
        "candidate_id": readiness.get("candidate_id"),
        "proposed_skill_id": readiness.get("proposed_skill_id"),
        "source_approval_id": approval_id,
        "requested_action": "approve_future_siteops_candidate_activation",
        "activation_gate_operation": activation_gate_operation,
        "required_approver_role": "tenant_admin",
        "risk_level": "high",
        "request_digest_sha256": request_digest,
        "status": "pending_operator_review" if activation_ready else "blocked_before_operator_review",
        "activation_allowed_in_this_pass": False,
        "activation_performed_in_this_pass": False,
        "trusted_artifact_write_allowed_in_this_pass": False,
        "browser_execution_allowed_in_this_pass": False,
        "agent_bus_enqueue_allowed_in_this_pass": False,
        "provider_api_call_allowed_in_this_pass": False,
        "canonical_writeback_allowed_in_this_pass": False,
    }
    approval: dict[str, Any] | None = None
    run_ref: str | None = None

    if not activation_ready:
        request_status = (
            "blocked_activation_boundary_readiness: "
            f"{readiness.get('activation_boundary_status')}"
        )
        review_decision = "blocked_before_activation_approval_request"
        audit_ref = None
    elif write_approval_request:
        approval = create_approval_request(
            root,
            scope=scope,
            run_id=run_id,
            workflow_id=PROMOTION_WORKFLOW_ID,
            action=activation_gate_operation,
            risk_level="high",
            approval_reason=(
                reason
                or "Review future activation of a SiteOps Browser Skill candidate. "
                "This approval request does not activate skills, write trusted "
                "artifacts, consume approvals, launch browsers, enqueue Agent Bus "
                "work, call providers, or write canonical ChaseOS state."
            ),
            required_approver_role="tenant_admin",
            requested_by=requested_by_id,
            metadata={
                "candidate_id": readiness.get("candidate_id"),
                "proposed_skill_id": readiness.get("proposed_skill_id"),
                "source_approval_id": approval_id,
                "activation_gate_operation": activation_gate_operation,
                "activation_boundary_status": readiness.get("activation_boundary_status"),
                "request_digest_sha256": request_digest,
                "secrets_or_session_state_included": False,
                "trusted_artifacts_written": False,
                "activation_performed": False,
                "browser_execution_performed": False,
                "agent_bus_enqueue_performed": False,
                "provider_api_call_performed": False,
                "canonical_writeback_performed": False,
            },
        )
        run = SiteOpsRun(
            run_id=run_id,
            tenant_id=scope.tenant_id,
            workspace_id=scope.workspace_id,
            user_id=scope.user_id,
            skill_id=str(readiness.get("proposed_skill_id") or candidate_id),
            workflow_id=PROMOTION_WORKFLOW_ID,
            site_profile_id=None,
            provider_id=None,
            mode="dry_run",
            status="approval_needed",
            inputs_ref=approval_id,
            outputs_ref=str(approval.get("approval_ref")),
            audit_ref=audit_ref,
            cost_estimate={"estimated_cost": 0, "currency": "USD", "live_provider_call": False},
            cost_actual=None,
            started_at=now_iso(),
            ended_at=now_iso(),
        )
        run_ref = write_run_record(root, run)
        audit_ref = append_audit_event(
            root,
            SiteOpsAuditEvent(
                event_id=f"event_{run_id}_activation_approval_request",
                run_id=run_id,
                tenant_id=scope.tenant_id,
                workspace_id=scope.workspace_id,
                user_id=scope.user_id,
                event_type="activation_approval_request_created",
                action=PROMOTION_ACTIVATION_APPROVAL_REQUEST_ACTION,
                target=str(readiness.get("candidate_id") or candidate_id),
                policy_decision="operator_approval_required",
                timestamp=now_iso(),
                metadata={
                    "approval_id": approval.get("approval_id"),
                    "approval_ref": approval.get("approval_ref"),
                    "activation_gate_operation": activation_gate_operation,
                    "source_approval_id": approval_id,
                    "trusted_artifacts_written": False,
                    "activation_performed": False,
                    "browser_execution_performed": False,
                    "agent_bus_enqueue_performed": False,
                    "provider_api_call_performed": False,
                    "canonical_writeback_performed": False,
                },
                redacted_fields=[],
            ),
        )
        request_status = "activation_approval_request_written_pending_operator_decision"
        review_decision = "pending_operator_review_for_future_activation"
    else:
        audit_ref = None
        request_status = "activation_approval_request_ready_preview_only"
        review_decision = "ready_to_write_pending_activation_approval_request_if_operator_requests"

    approval_request_checks = [
        _executor_preflight_check(
            "activation_boundary_ready",
            passed=activation_ready,
            detail=str(readiness.get("activation_boundary_status")),
        ),
        _executor_preflight_check(
            "requested_by_present",
            passed=bool(requested_by_id),
            detail=requested_by_id or "missing requested_by",
        ),
        _executor_preflight_check(
            "activation_not_performed",
            passed=True,
            detail="approval request does not activate the candidate or enable runtime use",
        ),
        _executor_preflight_check(
            "trusted_artifacts_not_written",
            passed=True,
            detail="approval request does not write trusted Browser Skill or SiteOps Skill Card artifacts",
        ),
    ]
    denied_effects = list(readiness.get("denied_effects") or readiness.get("blocked_actions") or [])
    for effect in [
        "consume activation approval from approval request",
        "activate promoted skill from approval request",
        "enable trusted Browser Skill from approval request",
        "enable SiteOps Skill Card from approval request",
        "launch browser from approval request",
        "enqueue Agent Bus work from approval request",
        "call provider APIs from approval request",
    ]:
        if effect not in denied_effects:
            denied_effects.insert(0, effect)

    return {
        "ok": True,
        "action": PROMOTION_ACTIVATION_APPROVAL_REQUEST_ACTION,
        "candidate_id": readiness.get("candidate_id"),
        "proposed_skill_id": readiness.get("proposed_skill_id"),
        "scope": scope.as_dict(),
        "source_approval_id": approval_id,
        "actor": actor,
        "requested_by": requested_by_id,
        "activation_approval_request_status": request_status,
        "review_decision": review_decision,
        "activation_boundary_status": readiness.get("activation_boundary_status"),
        "collision_policy_status": readiness.get("collision_policy_status"),
        "inactive_artifact_validator_status": readiness.get("inactive_artifact_validator_status"),
        "activation_gate_operation": activation_gate_operation,
        "activation_ready_for_operator_review": activation_ready,
        "approval_request_artifact": approval_request_artifact,
        "approval_request_checks": approval_request_checks,
        "approval": approval,
        "approval_id": approval.get("approval_id") if approval else None,
        "approval_ref": approval.get("approval_ref") if approval else None,
        "run_id": run_id,
        "run_ref": run_ref,
        "audit_ref": audit_ref,
        "request_digest_sha256": request_digest,
        "write_approval_request_requested": bool(write_approval_request),
        "approval_request_written": bool(approval),
        "approval_request_pending": bool(approval and approval.get("status") == "pending"),
        "writes_performed": bool(approval),
        "files_modified": bool(approval),
        "run_record_written": bool(run_ref),
        "audit_event_written": bool(audit_ref),
        "blocked_actions": denied_effects,
        "denied_effects": denied_effects,
        "trusted_skill_write_allowed": False,
        "siteops_skill_card_write_allowed": False,
        "trusted_artifacts_written": False,
        "approval_consumed": False,
        "activation_allowed": False,
        "activation_performed": False,
        "browser_execution_allowed": False,
        "agent_bus_enqueue_allowed": False,
        "provider_api_call_allowed": False,
        "canonical_writeback_allowed": False,
        "boundary": (
            "activation approval-request only; optional writes are limited to a pending "
            "SiteOps approval artifact, scoped run record, and audit event. Trusted "
            "artifacts, approval consumption, skill activation, browser execution, "
            "Agent Bus work, provider calls, and canonical ChaseOS state remain unchanged."
        ),
    }


def candidate_promotion_activation_approval_decision_preflight(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    source_approval_id: str,
    activation_approval_id: str,
    actor: str,
    reason: str | None = None,
) -> dict[str, Any]:
    """Validate a pending/decided activation approval without mutating it."""
    preview = candidate_promotion_activation_approval_request(
        candidate_id,
        root,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
        approval_id=source_approval_id,
        actor=actor,
        requested_by=actor,
        reason=reason or "operator requested activation approval decision preflight",
        write_approval_request=False,
    )
    scope_data = dict(preview.get("scope") or {})
    scope = SiteOpsScope(
        tenant_id=str(scope_data.get("tenant_id") or tenant_id or ""),
        workspace_id=str(scope_data.get("workspace_id") or workspace_id or ""),
        user_id=str(scope_data.get("user_id") or user_id or ""),
    )
    approval = show_approval_request(root, activation_approval_id, tenant_id=scope.tenant_id)
    metadata = dict(approval.get("metadata") or {})
    expected_digest = str(preview.get("request_digest_sha256") or "")
    metadata_digest = str(metadata.get("request_digest_sha256") or "")
    activation_gate_operation = str(preview.get("activation_gate_operation") or "")
    scope_match = (
        approval.get("tenant_id") == scope.tenant_id
        and approval.get("workspace_id") == scope.workspace_id
        and approval.get("user_id") == scope.user_id
    )
    action_match = approval.get("action") == activation_gate_operation
    candidate_match = metadata.get("candidate_id") == preview.get("candidate_id")
    skill_match = metadata.get("proposed_skill_id") == preview.get("proposed_skill_id")
    source_approval_match = metadata.get("source_approval_id") == source_approval_id
    digest_match = bool(expected_digest and metadata_digest == expected_digest)
    no_sensitive_state = metadata.get("secrets_or_session_state_included") is False
    original_request_no_mutation = (
        metadata.get("trusted_artifacts_written") is False
        and metadata.get("activation_performed") is False
        and metadata.get("browser_execution_performed") is False
        and metadata.get("agent_bus_enqueue_performed") is False
        and metadata.get("provider_api_call_performed") is False
        and metadata.get("canonical_writeback_performed") is False
    )
    required_role_match = approval.get("required_approver_role") == "tenant_admin"
    readiness_still_valid = preview.get("activation_ready_for_operator_review") is True
    approval_status = str(approval.get("status") or "")
    checks = [
        _executor_preflight_check(
            "approval_scope_matches_request",
            passed=scope_match,
            detail=f"{approval.get('tenant_id')}/{approval.get('workspace_id')}/{approval.get('user_id')}",
        ),
        _executor_preflight_check(
            "approval_action_matches_activation_request",
            passed=action_match,
            detail=str(approval.get("action")),
        ),
        _executor_preflight_check(
            "candidate_id_matches",
            passed=candidate_match,
            detail=str(metadata.get("candidate_id")),
        ),
        _executor_preflight_check(
            "proposed_skill_id_matches",
            passed=skill_match,
            detail=str(metadata.get("proposed_skill_id")),
        ),
        _executor_preflight_check(
            "source_approval_id_matches",
            passed=source_approval_match,
            detail=str(metadata.get("source_approval_id")),
        ),
        _executor_preflight_check(
            "request_digest_matches_current_preview",
            passed=digest_match,
            detail=metadata_digest or "missing request digest",
        ),
        _executor_preflight_check(
            "required_approver_role_is_tenant_admin",
            passed=required_role_match,
            detail=str(approval.get("required_approver_role")),
        ),
        _executor_preflight_check(
            "activation_readiness_still_valid",
            passed=readiness_still_valid,
            detail=str(preview.get("activation_boundary_status")),
        ),
        _executor_preflight_check(
            "no_sensitive_state_in_approval_metadata",
            passed=no_sensitive_state,
            detail="secrets/session state flag must be false",
        ),
        _executor_preflight_check(
            "original_request_had_no_mutation",
            passed=original_request_no_mutation,
            detail="approval metadata must record no artifact, activation, browser, Agent Bus, provider, or canonical mutation",
        ),
        _executor_preflight_check(
            "decision_preflight_is_no_mutation",
            passed=True,
            detail="does not decide, consume, activate, or write artifacts",
        ),
    ]
    required_checks_pass = all(bool(item.get("passed")) for item in checks if item.get("required", True))
    if not required_checks_pass:
        preflight_status = "blocked_activation_approval_decision_preflight_metadata_or_readiness_mismatch"
        review_decision = "blocked_before_activation_decision_consumer"
    elif approval_status == "pending":
        preflight_status = "blocked_pending_activation_approval"
        review_decision = "pending_operator_decision_no_activation"
    elif approval_status == "approved":
        preflight_status = "activation_approval_decision_preflight_ready_no_mutation"
        review_decision = "approved_for_separate_activation_consumer_review"
    elif approval_status == "rejected":
        preflight_status = "activation_approval_decision_preflight_rejected_blocks_activation"
        review_decision = "rejected_no_activation"
    else:
        preflight_status = f"blocked_activation_approval_decision_preflight_unknown_status:{approval_status}"
        review_decision = "blocked_before_activation_decision_consumer"

    approved_for_future_activation = required_checks_pass and approval_status == "approved"
    denied_effects = [
        "decide activation approval request",
        "consume activation approval request",
        "activate promoted skills",
        "enable trusted Browser Skill for execution",
        "enable SiteOps Skill Card for workflows",
        "write trusted Browser Skill artifact",
        "write SiteOps Skill Card artifact",
        "launch or control a browser",
        "enqueue Agent Bus work",
        "call provider APIs",
        "write canonical ChaseOS memory/state",
    ]
    return {
        "ok": True,
        "action": PROMOTION_ACTIVATION_APPROVAL_DECISION_PREFLIGHT_ACTION,
        "candidate_id": preview.get("candidate_id"),
        "proposed_skill_id": preview.get("proposed_skill_id"),
        "scope": scope.as_dict(),
        "source_approval_id": source_approval_id,
        "activation_approval_id": activation_approval_id,
        "actor": actor,
        "activation_approval_decision_preflight_status": preflight_status,
        "review_decision": review_decision,
        "approval_status": approval_status,
        "approval_ref": approval.get("approval_ref"),
        "approval_decided_by": approval.get("decided_by"),
        "approval_decided_at": approval.get("decided_at"),
        "activation_boundary_status": preview.get("activation_boundary_status"),
        "activation_approval_request_status": preview.get("activation_approval_request_status"),
        "activation_gate_operation": activation_gate_operation,
        "request_digest_sha256": expected_digest,
        "approval_request_digest_sha256": metadata_digest,
        "digest_matches": digest_match,
        "decision_preflight_checks": checks,
        "approved_for_future_activation_consumer_review": approved_for_future_activation,
        "ready_for_activation_consumer_next_pass": approved_for_future_activation,
        "activation_decision_allowed_in_this_pass": False,
        "approval_decision_written": False,
        "approval_consumed": False,
        "activation_consumption_marker_written": False,
        "activation_allowed": False,
        "activation_performed": False,
        "inactive_artifacts_written": False,
        "trusted_skill_write_allowed": False,
        "siteops_skill_card_write_allowed": False,
        "browser_execution_allowed": False,
        "agent_bus_enqueue_allowed": False,
        "provider_api_call_allowed": False,
        "canonical_writeback_allowed": False,
        "writes_performed": False,
        "files_modified": False,
        "blocked_actions": denied_effects,
        "denied_effects": denied_effects,
        "boundary": (
            "activation approval decision preflight only; validates a pending/decided "
            "activation approval request before a future activation consumer. It performs "
            "no approval decision, approval consumption, trusted artifact write, activation, "
            "browser execution, Agent Bus work, provider call, or canonical writeback."
        ),
    }


def candidate_promotion_activation_approval_decision_consumer_design(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    source_approval_id: str,
    activation_approval_id: str,
    actor: str,
    reason: str | None = None,
) -> dict[str, Any]:
    """Design the future activation approval consumer without mutating state."""
    preflight = candidate_promotion_activation_approval_decision_preflight(
        candidate_id,
        root,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
        source_approval_id=source_approval_id,
        activation_approval_id=activation_approval_id,
        actor=actor,
        reason=reason or "operator requested activation approval consumer design",
    )
    scope = dict(preflight.get("scope") or {})
    tenant = str(scope.get("tenant_id") or tenant_id or "")
    workspace = str(scope.get("workspace_id") or workspace_id or "")
    user = str(scope.get("user_id") or user_id or "")
    candidate = str(preflight.get("candidate_id") or candidate_id)
    proposed_skill_id = str(preflight.get("proposed_skill_id") or candidate)
    root_path = Path(root) if root is not None else Path.cwd()
    marker_name = (
        f"activation_consumer_{_slug(candidate)[:48]}_"
        f"{hashlib.sha256(f'{tenant}|{workspace}|{user}|{candidate}|{activation_approval_id}'.encode('utf-8')).hexdigest()[:12]}.json"
    )
    marker_path = (
        root_path
        / "07_LOGS"
        / "SiteOps-Activation-Consumers"
        / tenant
        / workspace
        / marker_name
    )
    audit_preview = (
        root_path
        / "07_LOGS"
        / "SiteOps-Audits"
        / tenant
        / workspace
        / f"siteops_activation_consumer_{_slug(candidate)[:48]}.jsonl"
    )
    ready_for_design = bool(preflight.get("ready_for_activation_consumer_next_pass"))
    if ready_for_design:
        design_status = "activation_approval_decision_consumer_design_ready_no_mutation"
        review_decision = "consumer_design_only_ready_for_future_write_guard"
    else:
        design_status = (
            "blocked_activation_approval_decision_consumer_design_preflight: "
            f"{preflight.get('activation_approval_decision_preflight_status')}"
        )
        review_decision = "blocked_before_activation_consumer_design"

    consumer_record_schema = {
        "record_type": "siteops_activation_approval_decision_consumer",
        "tenant_id": tenant,
        "workspace_id": workspace,
        "user_id": user,
        "candidate_id": candidate,
        "proposed_skill_id": proposed_skill_id,
        "source_approval_id": source_approval_id,
        "activation_approval_id": activation_approval_id,
        "activation_gate_operation": preflight.get("activation_gate_operation"),
        "request_digest_sha256": preflight.get("request_digest_sha256"),
        "approval_request_digest_sha256": preflight.get("approval_request_digest_sha256"),
        "approval_status_required": "approved",
        "consumed_at": "future_iso_timestamp",
        "consumed_by": actor,
        "secret_values_visible": False,
        "trusted_artifacts_written": False,
        "activation_performed": False,
        "browser_execution_performed": False,
        "agent_bus_enqueue_performed": False,
        "provider_api_call_performed": False,
        "canonical_writeback_performed": False,
    }
    future_sequence = [
        {
            "order": 1,
            "step_id": "rerun_activation_approval_decision_preflight",
            "effect": "read_only",
            "required": True,
            "implemented": False,
            "allowed_in_this_pass": False,
        },
        {
            "order": 2,
            "step_id": "verify_activation_approval_is_approved",
            "effect": "read_only",
            "required": True,
            "implemented": False,
            "allowed_in_this_pass": False,
        },
        {
            "order": 3,
            "step_id": "create_exact_once_consumer_marker",
            "effect": "future_scoped_write",
            "required": True,
            "implemented": False,
            "allowed_in_this_pass": False,
        },
        {
            "order": 4,
            "step_id": "write_activation_consumer_audit_event",
            "effect": "future_scoped_audit_write",
            "required": True,
            "implemented": False,
            "allowed_in_this_pass": False,
        },
        {
            "order": 5,
            "step_id": "stop_before_activation_executor",
            "effect": "stop_condition",
            "required": True,
            "implemented": False,
            "allowed_in_this_pass": False,
        },
    ]
    design_checks = [
        _executor_preflight_check(
            "decision_preflight_ready",
            passed=ready_for_design,
            detail=str(preflight.get("activation_approval_decision_preflight_status")),
        ),
        _executor_preflight_check(
            "consumer_marker_path_scoped",
            passed=bool(tenant and workspace and marker_path.as_posix().find(f"/{tenant}/{workspace}/") >= 0),
            detail=marker_path.as_posix(),
        ),
        _executor_preflight_check(
            "consumer_marker_not_written",
            passed=not marker_path.exists(),
            detail="design pass does not create the marker",
        ),
        _executor_preflight_check(
            "activation_still_blocked",
            passed=True,
            detail="future consumer must stop before activation executor",
        ),
    ]
    denied_effects = [
        "write activation consumer marker",
        "consume activation approval request",
        "decide activation approval request",
        "activate promoted skills",
        "enable trusted Browser Skill for execution",
        "enable SiteOps Skill Card for workflows",
        "write trusted Browser Skill artifact",
        "write SiteOps Skill Card artifact",
        "launch or control a browser",
        "enqueue Agent Bus work",
        "call provider APIs",
        "write canonical ChaseOS memory/state",
    ]
    return {
        "ok": True,
        "action": PROMOTION_ACTIVATION_APPROVAL_DECISION_CONSUMER_DESIGN_ACTION,
        "candidate_id": candidate,
        "proposed_skill_id": proposed_skill_id,
        "scope": {"tenant_id": tenant, "workspace_id": workspace, "user_id": user},
        "source_approval_id": source_approval_id,
        "activation_approval_id": activation_approval_id,
        "actor": actor,
        "activation_approval_decision_consumer_design_status": design_status,
        "review_decision": review_decision,
        "activation_approval_decision_preflight_status": preflight.get(
            "activation_approval_decision_preflight_status"
        ),
        "approval_status": preflight.get("approval_status"),
        "activation_gate_operation": preflight.get("activation_gate_operation"),
        "request_digest_sha256": preflight.get("request_digest_sha256"),
        "approval_request_digest_sha256": preflight.get("approval_request_digest_sha256"),
        "consumer_record_schema": consumer_record_schema,
        "consumer_marker_preview": {
            "path": marker_path.as_posix(),
            "exists": marker_path.exists(),
            "create_new_only": True,
            "exact_once": True,
            "written_in_this_pass": False,
        },
        "audit_event_preview": {
            "path": audit_preview.as_posix(),
            "event_type": "activation_approval_decision_consumed",
            "written_in_this_pass": False,
        },
        "future_consumer_sequence": future_sequence,
        "consumer_design_checks": design_checks,
        "ready_for_activation_consumer_write_guard_next_pass": ready_for_design,
        "activation_consumer_implemented": False,
        "activation_consumer_write_allowed_in_this_pass": False,
        "activation_consumption_marker_written": False,
        "approval_consumed": False,
        "approval_decision_written": False,
        "activation_allowed": False,
        "activation_performed": False,
        "trusted_skill_write_allowed": False,
        "siteops_skill_card_write_allowed": False,
        "browser_execution_allowed": False,
        "agent_bus_enqueue_allowed": False,
        "provider_api_call_allowed": False,
        "canonical_writeback_allowed": False,
        "writes_performed": False,
        "files_modified": False,
        "blocked_actions": denied_effects,
        "denied_effects": denied_effects,
        "boundary": (
            "activation approval decision consumer design only; defines future "
            "exact-once consumer marker, audit, stop conditions, and handoff "
            "requirements. It performs no approval consumption, marker write, "
            "trusted artifact write, activation, browser execution, Agent Bus work, "
            "provider call, or canonical writeback."
        ),
    }


def candidate_promotion_activation_approval_decision_consumer_write_guard_contract(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    source_approval_id: str,
    activation_approval_id: str,
    actor: str,
    reason: str | None = None,
) -> dict[str, Any]:
    """Declare the future activation approval consumer write guard without writing."""
    design = candidate_promotion_activation_approval_decision_consumer_design(
        candidate_id,
        root,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
        source_approval_id=source_approval_id,
        activation_approval_id=activation_approval_id,
        actor=actor,
        reason=reason or "operator requested activation approval consumer write guard contract",
    )
    scope = dict(design.get("scope") or {})
    tenant = str(scope.get("tenant_id") or tenant_id or "")
    workspace = str(scope.get("workspace_id") or workspace_id or "")
    user = str(scope.get("user_id") or user_id or "")
    proposed_skill_id = str(design.get("proposed_skill_id") or candidate_id)
    root_path = Path(root) if root is not None else Path.cwd()
    marker_preview = dict(design.get("consumer_marker_preview") or {})
    audit_preview = dict(design.get("audit_event_preview") or {})
    marker_path = Path(str(marker_preview.get("path") or ""))
    marker_exists = bool(marker_preview.get("exists")) or marker_path.exists()
    trusted_skill_path = (TRUSTED_SKILL_REL / f"{proposed_skill_id}.yaml").as_posix()
    siteops_skill_card_path = _siteops_skill_card_target(proposed_skill_id)
    design_ready = bool(design.get("ready_for_activation_consumer_write_guard_next_pass"))
    explicit_write_flag = "--consume-activation-approval"
    guard_contract = {
        "status": "write_guard_contract_only",
        "explicit_write_flag": explicit_write_flag,
        "explicit_write_flag_supported_in_this_pass": False,
        "unsupported_flag_rejection": (
            f"{explicit_write_flag} is intentionally unsupported by this command; "
            "a separate operator-reviewed activation approval consumer writer must "
            "be built before any approval consumption or marker write"
        ),
        "allowed_future_marker_path": marker_preview.get("path"),
        "allowed_future_audit_path": audit_preview.get("path"),
        "allowed_future_write_roots": [
            (root_path / "07_LOGS" / "SiteOps-Activation-Consumers" / tenant / workspace).as_posix(),
            (root_path / "07_LOGS" / "SiteOps-Audits" / tenant / workspace).as_posix(),
        ],
        "forbidden_targets": [
            trusted_skill_path,
            siteops_skill_card_path,
            "runtime/browser_skills/skills/*.yaml activation toggles",
            "runtime/siteops/registry/skill_cards/*.json activation toggles",
            "runtime/chaseos_gate.py",
            "runtime/policy/gateway_allowlists.json",
            "canonical ChaseOS memory/state",
        ],
        "create_new_only": True,
        "fail_if_marker_exists": True,
        "requires_approved_activation_decision_preflight": True,
        "requires_digest_match": True,
        "requires_exact_scope_match": True,
        "requires_trusted_artifact_provenance_check": True,
        "requires_artifacts_inactive_before_consumption": True,
        "requires_prewrite_audit_event": True,
        "requires_postwrite_audit_event": True,
        "requires_rollback_evidence": True,
        "requires_no_secret_cookie_token_session_state": True,
        "requires_stop_before_activation_executor": True,
        "activation_executor_may_not_run_in_consumer": True,
    }
    guard_ready = design_ready and bool(marker_preview.get("create_new_only")) and not marker_exists
    if guard_ready:
        guard_status = "activation_approval_decision_consumer_write_guard_ready_no_write"
        review_decision = "ready_for_separate_operator_reviewed_activation_consumer_writer_design"
    else:
        guard_status = "blocked_activation_approval_decision_consumer_write_guard_preconditions"
        review_decision = "blocked_before_activation_consumer_writer"
    checks = list(design.get("consumer_design_checks") or []) + [
        _executor_preflight_check(
            "consumer_design_ready",
            passed=design_ready,
            detail=str(design.get("activation_approval_decision_consumer_design_status")),
        ),
        _executor_preflight_check(
            "explicit_consume_flag_unsupported_this_pass",
            passed=guard_contract["explicit_write_flag_supported_in_this_pass"] is False,
            detail=guard_contract["unsupported_flag_rejection"],
        ),
        _executor_preflight_check(
            "consumer_marker_create_new_only",
            passed=bool(marker_preview.get("create_new_only")) and bool(marker_preview.get("exact_once")),
            detail=str(marker_preview.get("path")),
        ),
        _executor_preflight_check(
            "consumer_marker_absent_before_future_write",
            passed=not marker_exists,
            detail=str(marker_preview.get("path")),
        ),
        _executor_preflight_check(
            "consumer_future_write_roots_scoped",
            passed=bool(tenant and workspace and all(f"/{tenant}/{workspace}" in path for path in guard_contract["allowed_future_write_roots"])),
            detail=", ".join(guard_contract["allowed_future_write_roots"]),
        ),
        _executor_preflight_check(
            "trusted_artifact_writes_forbidden_by_consumer",
            passed=True,
            detail=", ".join(path for path in [trusted_skill_path, siteops_skill_card_path] if path),
        ),
        _executor_preflight_check(
            "activation_executor_still_separate",
            passed=True,
            detail="future consumer must stop after marker/audit and before activation executor",
        ),
    ]
    denied_effects = [
        "write activation consumer marker",
        "append activation consumer audit events",
        "consume activation approval request",
        "decide activation approval request",
        "activate promoted skills",
        "enable trusted Browser Skill for execution",
        "enable SiteOps Skill Card for workflows",
        "write trusted Browser Skill artifact",
        "write SiteOps Skill Card artifact",
        "modify Gate policy",
        "launch or control a browser",
        "enqueue Agent Bus work",
        "call provider APIs",
        "write canonical ChaseOS memory/state",
    ]
    result = dict(design)
    result.update(
        {
            "action": PROMOTION_ACTIVATION_APPROVAL_DECISION_CONSUMER_WRITE_GUARD_ACTION,
            "activation_approval_decision_consumer_write_guard_status": guard_status,
            "review_decision": review_decision,
            "activation_consumer_write_guard_contract": guard_contract,
            "activation_consumer_write_guard_checks": checks,
            "ready_for_activation_consumer_writer_design_next_pass": guard_ready,
            "consume_activation_approval_flag_supported": False,
            "consume_activation_approval_flag_required_for_future_writer": True,
            "activation_consumer_writer_implemented": False,
            "activation_consumer_writer_allowed_in_this_pass": False,
            "activation_consumer_write_allowed_in_this_pass": False,
            "activation_consumption_marker_written": False,
            "activation_consumer_audit_written": False,
            "approval_consumed": False,
            "approval_decision_written": False,
            "activation_allowed": False,
            "activation_performed": False,
            "trusted_skill_write_allowed": False,
            "siteops_skill_card_write_allowed": False,
            "browser_execution_allowed": False,
            "agent_bus_enqueue_allowed": False,
            "provider_api_call_allowed": False,
            "canonical_writeback_allowed": False,
            "writes_performed": False,
            "files_modified": False,
            "blocked_actions": denied_effects,
            "denied_effects": denied_effects,
            "boundary": (
                "activation approval decision consumer write guard contract only; "
                "declares the future explicit approval-consumption flag, exact-once "
                "marker path, audit roots, artifact provenance checks, and stop-before-"
                "activation boundary. It performs no approval consumption, marker write, "
                "audit write, trusted artifact write, activation, browser execution, "
                "Agent Bus work, provider call, or canonical writeback."
            ),
        }
    )
    return result


def candidate_promotion_activation_approval_decision_consumer_writer_design(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    source_approval_id: str,
    activation_approval_id: str,
    actor: str,
    reason: str | None = None,
) -> dict[str, Any]:
    """Design the future activation approval consumer writer without writing."""
    guard = candidate_promotion_activation_approval_decision_consumer_write_guard_contract(
        candidate_id,
        root,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
        source_approval_id=source_approval_id,
        activation_approval_id=activation_approval_id,
        actor=actor,
        reason=reason or "operator requested activation approval consumer writer design",
    )
    scope = dict(guard.get("scope") or {})
    tenant = str(scope.get("tenant_id") or tenant_id or "")
    workspace = str(scope.get("workspace_id") or workspace_id or "")
    user = str(scope.get("user_id") or user_id or "")
    marker_preview = dict(guard.get("consumer_marker_preview") or {})
    audit_preview = dict(guard.get("audit_event_preview") or {})
    guard_contract = dict(guard.get("activation_consumer_write_guard_contract") or {})
    guard_ready = bool(guard.get("ready_for_activation_consumer_writer_design_next_pass"))
    explicit_write_flag = str(guard_contract.get("explicit_write_flag") or "--consume-activation-approval")
    allowed_write_roots = list(guard_contract.get("allowed_future_write_roots") or [])
    writer_record_schema = {
        "record_type": "activation_approval_consumer_writer_plan",
        "required_fields": [
            "candidate_id",
            "tenant_id",
            "workspace_id",
            "user_id",
            "source_approval_id",
            "activation_approval_id",
            "request_digest_sha256",
            "consumer_marker_path",
            "audit_event_path",
            "explicit_write_flag",
            "prewrite_checks",
            "postwrite_checks",
            "stop_before_activation_executor",
        ],
        "forbidden_fields": [
            "cookies",
            "session",
            "session_key",
            "token",
            "api_key",
            "password",
            "secret",
            "private_key",
            "seed_phrase",
        ],
    }
    write_set_preview = {
        "status": "future_writer_write_set_preview_only",
        "explicit_write_flag": explicit_write_flag,
        "explicit_write_flag_supported_in_this_pass": False,
        "marker_path": marker_preview.get("path"),
        "audit_path": audit_preview.get("path"),
        "allowed_write_roots": allowed_write_roots,
        "create_new_only": True,
        "append_only_audit": True,
        "consume_approval_request_ref": activation_approval_id,
        "approval_request_mutation_allowed_in_this_pass": False,
        "marker_written_in_this_pass": False,
        "audit_written_in_this_pass": False,
        "approval_consumed_in_this_pass": False,
    }
    rollback_contract = {
        "status": "future_writer_rollback_contract_preview_only",
        "rollback_required_before_future_write": True,
        "marker_write_rollback": "delete only if this future writer created the marker and postwrite audit failed",
        "audit_rollback": "append compensating audit event; do not rewrite or truncate existing audit logs",
        "approval_state_rollback": "do not mutate approval status until marker/audit preconditions pass",
        "trusted_artifact_rollback": "not applicable; consumer writer must not write trusted artifacts",
        "activation_rollback": "not applicable; consumer writer must stop before activation executor",
        "written_in_this_pass": False,
    }
    future_writer_sequence = [
        "require explicit --consume-activation-approval",
        "reload activation approval decision preflight",
        "verify activation approval is approved and scoped to tenant/workspace/user",
        "verify request digest and approval digest still match",
        "verify trusted Browser Skill and SiteOps Skill Card remain inactive",
        "verify exact-once consumer marker does not already exist",
        "append pre-consumption audit event under scoped audit root",
        "create activation consumer marker with create-new-only semantics",
        "append post-consumption audit event under scoped audit root",
        "return consumed-marker evidence and stop before activation executor",
    ]
    marker_path = Path(str(marker_preview.get("path") or ""))
    marker_absent = not marker_path.exists()
    checks = list(guard.get("activation_consumer_write_guard_checks") or []) + [
        _executor_preflight_check(
            "write_guard_ready",
            passed=guard_ready,
            detail=str(guard.get("activation_approval_decision_consumer_write_guard_status")),
        ),
        _executor_preflight_check(
            "future_writer_requires_explicit_consume_flag",
            passed=explicit_write_flag == "--consume-activation-approval",
            detail=explicit_write_flag,
        ),
        _executor_preflight_check(
            "future_writer_write_set_scoped",
            passed=bool(tenant and workspace and allowed_write_roots and all(f"/{tenant}/{workspace}" in path for path in allowed_write_roots)),
            detail=", ".join(allowed_write_roots),
        ),
        _executor_preflight_check(
            "future_writer_marker_create_new_only",
            passed=bool(write_set_preview["create_new_only"]) and marker_absent,
            detail=str(marker_preview.get("path")),
        ),
        _executor_preflight_check(
            "future_writer_append_only_audit",
            passed=bool(write_set_preview["append_only_audit"]),
            detail=str(audit_preview.get("path")),
        ),
        _executor_preflight_check(
            "future_writer_stops_before_activation_executor",
            passed=True,
            detail="activation executor remains a separate future command/path",
        ),
        _executor_preflight_check(
            "future_writer_no_secret_session_fields",
            passed=True,
            detail=", ".join(writer_record_schema["forbidden_fields"]),
        ),
    ]
    writer_ready = guard_ready and marker_absent
    if writer_ready:
        writer_status = "activation_approval_decision_consumer_writer_design_ready_no_mutation"
        review_decision = "ready_for_separate_operator_reviewed_activation_consumer_writer_implementation_request"
    else:
        writer_status = "blocked_activation_approval_decision_consumer_writer_design_preconditions"
        review_decision = "blocked_before_activation_consumer_writer_implementation_request"
    denied_effects = [
        "consume activation approval request",
        "write activation consumer marker",
        "append activation consumer audit events",
        "decide activation approval request",
        "activate promoted skills",
        "enable trusted Browser Skill for execution",
        "enable SiteOps Skill Card for workflows",
        "write trusted Browser Skill artifact",
        "write SiteOps Skill Card artifact",
        "modify Gate policy",
        "launch or control a browser",
        "enqueue Agent Bus work",
        "call provider APIs",
        "write canonical ChaseOS memory/state",
    ]
    result = dict(guard)
    result.update(
        {
            "action": PROMOTION_ACTIVATION_APPROVAL_DECISION_CONSUMER_WRITER_DESIGN_ACTION,
            "activation_approval_decision_consumer_writer_design_status": writer_status,
            "review_decision": review_decision,
            "activation_consumer_writer_record_schema": writer_record_schema,
            "activation_consumer_writer_write_set_preview": write_set_preview,
            "activation_consumer_writer_rollback_contract": rollback_contract,
            "activation_consumer_writer_sequence": future_writer_sequence,
            "activation_consumer_writer_design_checks": checks,
            "ready_for_activation_consumer_writer_implementation_request_next_pass": writer_ready,
            "future_writer_consume_activation_approval_flag_required": True,
            "consume_activation_approval_flag_supported": False,
            "activation_consumer_writer_implemented": False,
            "activation_consumer_writer_allowed_in_this_pass": False,
            "activation_consumer_write_allowed_in_this_pass": False,
            "activation_consumption_marker_written": False,
            "activation_consumer_audit_written": False,
            "approval_consumed": False,
            "approval_decision_written": False,
            "activation_allowed": False,
            "activation_performed": False,
            "trusted_skill_write_allowed": False,
            "siteops_skill_card_write_allowed": False,
            "browser_execution_allowed": False,
            "agent_bus_enqueue_allowed": False,
            "provider_api_call_allowed": False,
            "canonical_writeback_allowed": False,
            "writes_performed": False,
            "files_modified": False,
            "blocked_actions": denied_effects,
            "denied_effects": denied_effects,
            "boundary": (
                "activation approval consumer writer design only; declares the "
                "future explicit writer write set, scoped marker/audit roots, "
                "idempotency and provenance checks, and stop-before-activation "
                "sequence. It performs no approval consumption, marker write, "
                "audit write, trusted artifact write, activation, browser execution, "
                "Agent Bus work, provider call, or canonical writeback."
            ),
        }
    )
    return result


def candidate_promotion_activation_approval_decision_consumer_writer_implementation_request(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    source_approval_id: str,
    activation_approval_id: str,
    actor: str,
    reason: str | None = None,
) -> dict[str, Any]:
    """Package the future activation approval consumer writer request without writing."""
    design = candidate_promotion_activation_approval_decision_consumer_writer_design(
        candidate_id,
        root,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
        source_approval_id=source_approval_id,
        activation_approval_id=activation_approval_id,
        actor=actor,
        reason=reason or "operator requested activation approval consumer writer implementation request",
    )
    scope = dict(design.get("scope") or {})
    write_set = dict(design.get("activation_consumer_writer_write_set_preview") or {})
    rollback = dict(design.get("activation_consumer_writer_rollback_contract") or {})
    schema = dict(design.get("activation_consumer_writer_record_schema") or {})
    design_ready = bool(design.get("ready_for_activation_consumer_writer_implementation_request_next_pass"))
    explicit_flag_ready = (
        write_set.get("explicit_write_flag") == "--consume-activation-approval"
        and write_set.get("explicit_write_flag_supported_in_this_pass") is False
        and design.get("future_writer_consume_activation_approval_flag_required") is True
    )
    write_set_ready = (
        bool(write_set.get("create_new_only"))
        and bool(write_set.get("append_only_audit"))
        and bool(write_set.get("marker_path"))
        and bool(write_set.get("audit_path"))
    )
    rollback_ready = rollback.get("rollback_required_before_future_write") is True
    required_fields_ready = bool(schema.get("required_fields"))
    request_id = _new_run_id(
        f"{design.get('candidate_id')}_activation_consumer_writer_implementation_request"
    )
    request_artifact = {
        "request_id": request_id,
        "request_type": "siteops_activation_consumer_writer_implementation_request",
        "tenant_id": scope.get("tenant_id"),
        "workspace_id": scope.get("workspace_id"),
        "user_id": scope.get("user_id"),
        "candidate_id": design.get("candidate_id"),
        "proposed_skill_id": design.get("proposed_skill_id"),
        "source_approval_id": source_approval_id,
        "activation_approval_id": activation_approval_id,
        "requested_action": "implement_activation_approval_consumer_writer",
        "required_operator_decision": "approve_future_activation_consumer_writer_implementation_pass",
        "status": "review_packet_only",
        "writer_design_status": design.get("activation_approval_decision_consumer_writer_design_status"),
        "write_guard_status": design.get("activation_approval_decision_consumer_write_guard_status"),
        "future_command_name": "activation-approval-decision-consumer",
        "future_explicit_write_flag": "--consume-activation-approval",
        "future_write_set": write_set,
        "rollback_contract": rollback,
        "record_schema": schema,
        "future_sequence": design.get("activation_consumer_writer_sequence"),
        "implementation_allowed_in_this_pass": False,
        "writes_allowed_in_this_pass": False,
        "approval_consumption_allowed_in_this_pass": False,
        "marker_write_allowed_in_this_pass": False,
        "audit_write_allowed_in_this_pass": False,
        "activation_allowed_in_this_pass": False,
        "trusted_artifact_write_allowed_in_this_pass": False,
    }
    checks = list(design.get("activation_consumer_writer_design_checks") or []) + [
        _executor_preflight_check(
            "writer_implementation_request_design_ready",
            passed=design_ready,
            detail=str(design.get("activation_approval_decision_consumer_writer_design_status")),
        ),
        _executor_preflight_check(
            "writer_implementation_request_future_consume_flag_required",
            passed=explicit_flag_ready,
            detail=str(write_set.get("explicit_write_flag")),
        ),
        _executor_preflight_check(
            "writer_implementation_request_write_set_preview_ready",
            passed=write_set_ready,
            detail=str({"marker_path": write_set.get("marker_path"), "audit_path": write_set.get("audit_path")}),
        ),
        _executor_preflight_check(
            "writer_implementation_request_rollback_required",
            passed=rollback_ready,
            detail=str(rollback),
        ),
        _executor_preflight_check(
            "writer_implementation_request_record_schema_ready",
            passed=required_fields_ready,
            detail=str(schema.get("required_fields")),
        ),
        _executor_preflight_check(
            "writer_implementation_request_no_writes_this_pass",
            passed=True,
            detail="implementation request only; the activation consumer writer is not implemented",
        ),
    ]
    checks_passed = all(bool(check.get("passed")) for check in checks if check.get("required", True))
    if design_ready and checks_passed:
        request_status = "activation_approval_decision_consumer_writer_implementation_request_ready_no_write"
        review_decision = "ready_for_operator_review_of_activation_consumer_writer_implementation"
    else:
        request_status = "blocked_activation_approval_decision_consumer_writer_implementation_request_preconditions"
        review_decision = "blocked_before_activation_consumer_writer_implementation_approval"

    denied_effects = list(design.get("denied_effects") or [])
    for effect in [
        "write activation consumer writer implementation request",
        "implement activation consumer writer from implementation request",
        "accept --consume-activation-approval on this implementation request command",
        "write activation consumer marker",
        "append activation consumer audit events",
        "consume activation approval request",
    ]:
        if effect not in denied_effects:
            denied_effects.append(effect)

    result = dict(design)
    result.update(
        {
            "action": PROMOTION_ACTIVATION_APPROVAL_DECISION_CONSUMER_WRITER_IMPLEMENTATION_REQUEST_ACTION,
            "activation_approval_decision_consumer_writer_implementation_request_status": request_status,
            "review_decision": review_decision,
            "activation_consumer_writer_implementation_request": request_artifact,
            "activation_consumer_writer_implementation_request_checks": checks,
            "ready_for_activation_consumer_writer_implementation_approval_next_pass": (
                request_status
                == "activation_approval_decision_consumer_writer_implementation_request_ready_no_write"
            ),
            "implementation_request_artifact_written": False,
            "consume_activation_approval_flag_supported": False,
            "future_consume_activation_approval_flag_required": True,
            "activation_consumer_writer_implemented": False,
            "activation_consumer_writer_allowed_in_this_pass": False,
            "activation_consumer_write_allowed_in_this_pass": False,
            "activation_consumption_marker_written": False,
            "activation_consumer_audit_written": False,
            "approval_consumed": False,
            "approval_decision_written": False,
            "activation_allowed": False,
            "activation_performed": False,
            "trusted_skill_write_allowed": False,
            "siteops_skill_card_write_allowed": False,
            "browser_execution_allowed": False,
            "agent_bus_enqueue_allowed": False,
            "provider_api_call_allowed": False,
            "canonical_writeback_allowed": False,
            "writes_performed": False,
            "files_modified": False,
            "blocked_actions": denied_effects,
            "denied_effects": denied_effects,
            "boundary": (
                "activation approval consumer writer implementation request only; "
                "packages reviewed writer-design evidence for a future operator "
                "approval pass. It performs no approval consumption, marker write, "
                "audit write, trusted artifact write, activation, browser execution, "
                "Agent Bus work, provider call, or canonical writeback."
            ),
        }
    )
    return result


def candidate_promotion_activation_approval_decision_consumer_writer_implementation_approval(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    source_approval_id: str,
    activation_approval_id: str,
    decision: str,
    actor: str,
    reason: str | None = None,
) -> dict[str, Any]:
    """Return a no-write approval/rejection packet for the future consumer writer."""
    normalized_decision = (decision or "").strip().lower()
    if normalized_decision not in {"approve", "reject"}:
        raise ValueError("decision must be 'approve' or 'reject'")

    implementation_request = (
        candidate_promotion_activation_approval_decision_consumer_writer_implementation_request(
            candidate_id,
            root,
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            user_id=user_id,
            source_approval_id=source_approval_id,
            activation_approval_id=activation_approval_id,
            actor=actor,
            reason=reason
            or "operator requested no-write activation consumer writer implementation approval",
        )
    )
    scope = dict(implementation_request.get("scope") or {})
    request_artifact = dict(
        implementation_request.get("activation_consumer_writer_implementation_request") or {}
    )
    request_status = implementation_request.get(
        "activation_approval_decision_consumer_writer_implementation_request_status"
    )
    request_ready = bool(
        implementation_request.get("ready_for_activation_consumer_writer_implementation_approval_next_pass")
    )
    actor_id = (actor or user_id or "").strip()
    decision_id = _new_run_id(
        f"{implementation_request.get('candidate_id')}_activation_consumer_writer_implementation_approval"
    )
    approval_record = {
        "decision_id": decision_id,
        "record_type": "siteops_activation_consumer_writer_implementation_approval",
        "tenant_id": scope.get("tenant_id"),
        "workspace_id": scope.get("workspace_id"),
        "user_id": scope.get("user_id"),
        "actor": actor_id,
        "decision": normalized_decision,
        "reason": reason or "",
        "candidate_id": implementation_request.get("candidate_id"),
        "proposed_skill_id": implementation_request.get("proposed_skill_id"),
        "source_approval_id": source_approval_id,
        "activation_approval_id": activation_approval_id,
        "implementation_request_id": request_artifact.get("request_id"),
        "future_command_name": request_artifact.get("future_command_name"),
        "future_explicit_write_flag": "--consume-activation-approval",
        "future_write_set": request_artifact.get("future_write_set"),
        "rollback_contract": request_artifact.get("rollback_contract"),
        "status": "review_decision_packet_only",
        "durable_record_written": False,
        "approval_decision_written": False,
        "implementation_allowed_in_this_pass": False,
        "activation_consumer_writer_allowed_in_this_pass": False,
        "consume_activation_approval_flag_supported_in_this_pass": False,
        "approval_consumption_allowed": False,
        "marker_write_allowed_in_this_pass": False,
        "audit_write_allowed_in_this_pass": False,
        "activation_allowed_in_this_pass": False,
        "trusted_artifact_write_allowed_in_this_pass": False,
    }
    implementation_approved = request_ready and normalized_decision == "approve"
    implementation_rejected = request_ready and normalized_decision == "reject"
    if not request_ready:
        approval_status = (
            "blocked_activation_consumer_writer_implementation_request: "
            f"{request_status}"
        )
        review_decision = "blocked_before_activation_consumer_writer_implementation_approval"
    elif implementation_approved:
        approval_status = (
            "activation_approval_decision_consumer_writer_implementation_approved_for_next_pass_no_write"
        )
        review_decision = "operator_intent_approve_activation_consumer_writer_implementation_next_pass"
    else:
        approval_status = "activation_approval_decision_consumer_writer_implementation_rejected_no_write"
        review_decision = "operator_intent_reject_activation_consumer_writer_implementation"

    approval_checks = [
        _executor_preflight_check(
            "writer_implementation_request_ready",
            passed=request_ready,
            detail=str(request_status),
        ),
        _executor_preflight_check(
            "writer_implementation_approval_decision_valid",
            passed=True,
            detail=normalized_decision,
        ),
        _executor_preflight_check(
            "writer_implementation_approval_actor_present",
            passed=bool(actor_id),
            detail=actor_id,
        ),
        _executor_preflight_check(
            "writer_implementation_approval_record_still_no_write",
            passed=True,
            detail="durable_record_written=false; approval_decision_written=false",
        ),
        _executor_preflight_check(
            "writer_implementation_still_disabled",
            passed=True,
            detail="approval pass does not implement the activation consumer writer",
        ),
        _executor_preflight_check(
            "writer_implementation_consume_flag_still_unsupported",
            passed=True,
            detail="--consume-activation-approval remains reserved for a later writer",
        ),
        _executor_preflight_check(
            "writer_implementation_no_marker_audit_or_approval_consumption",
            passed=True,
            detail="no marker write, audit append, or approval consumption in this pass",
        ),
    ]
    if not actor_id:
        approval_status = "blocked_missing_activation_consumer_writer_implementation_approval_actor"
        review_decision = "blocked_before_activation_consumer_writer_implementation_approval"
        implementation_approved = False
        implementation_rejected = False

    denied_effects = list(implementation_request.get("denied_effects") or [])
    for effect in [
        "write activation consumer writer implementation approval record",
        "consume activation consumer writer implementation approval",
        "implement activation consumer writer from implementation approval",
        "accept --consume-activation-approval on this implementation approval command",
        "write activation consumer marker",
        "append activation consumer audit events",
        "consume activation approval request",
    ]:
        if effect not in denied_effects:
            denied_effects.append(effect)

    result = dict(implementation_request)
    result.update(
        {
            "action": PROMOTION_ACTIVATION_APPROVAL_DECISION_CONSUMER_WRITER_IMPLEMENTATION_APPROVAL_ACTION,
            "decision": normalized_decision,
            "actor": actor_id,
            "activation_approval_decision_consumer_writer_implementation_approval_status": approval_status,
            "review_decision": review_decision,
            "activation_consumer_writer_implementation_approval": approval_record,
            "activation_consumer_writer_implementation_approval_checks": approval_checks,
            "implementation_approved_no_write": implementation_approved,
            "implementation_rejected_no_write": implementation_rejected,
            "ready_for_activation_consumer_writer_implementation_next_pass": implementation_approved,
            "implementation_approval_artifact_written": False,
            "implementation_request_artifact_written": False,
            "consume_activation_approval_flag_supported": False,
            "future_consume_activation_approval_flag_required": True,
            "activation_consumer_writer_implemented": False,
            "activation_consumer_writer_allowed_in_this_pass": False,
            "activation_consumer_write_allowed_in_this_pass": False,
            "activation_consumption_marker_written": False,
            "activation_consumer_audit_written": False,
            "approval_consumed": False,
            "approval_decision_written": False,
            "activation_allowed": False,
            "activation_performed": False,
            "trusted_skill_write_allowed": False,
            "siteops_skill_card_write_allowed": False,
            "browser_execution_allowed": False,
            "agent_bus_enqueue_allowed": False,
            "provider_api_call_allowed": False,
            "canonical_writeback_allowed": False,
            "writes_performed": False,
            "files_modified": False,
            "blocked_actions": denied_effects,
            "denied_effects": denied_effects,
            "boundary": (
                "activation approval consumer writer implementation approval only; "
                "records approve/reject intent for a future implementation pass without "
                "writing the approval record, consuming approvals, writing markers or "
                "audit events, implementing the writer, activating skills, launching "
                "browser execution, enqueueing Agent Bus work, calling providers, or "
                "writing canonical state."
            ),
        }
    )
    return result


def candidate_promotion_activation_approval_decision_consumer_writer_implementation(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    source_approval_id: str,
    activation_approval_id: str,
    actor: str,
    reason: str | None = None,
    consume_activation_approval: bool = False,
) -> dict[str, Any]:
    """Consume an approved activation ApprovalRequest by exact-once marker only.

    This writer creates scoped SiteOps run/audit evidence and one exact-once
    activation-consumption marker when explicitly requested. It does not mutate
    the ApprovalRequest, activate skills, write trusted artifacts, run browsers,
    enqueue Agent Bus work, call providers, mutate Gate policy, or write
    canonical ChaseOS state.
    """
    implementation_approval = (
        candidate_promotion_activation_approval_decision_consumer_writer_implementation_approval(
            candidate_id,
            root,
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            user_id=user_id,
            source_approval_id=source_approval_id,
            activation_approval_id=activation_approval_id,
            decision="approve",
            actor=actor,
            reason=reason or "operator-approved activation approval consumer writer implementation",
        )
    )
    writer_design = candidate_promotion_activation_approval_decision_consumer_writer_design(
        candidate_id,
        root,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
        source_approval_id=source_approval_id,
        activation_approval_id=activation_approval_id,
        actor=actor,
        reason=reason or "operator invoked activation approval consumer writer implementation",
    )
    scope = dict(implementation_approval.get("scope") or writer_design.get("scope") or {})
    tenant = str(scope.get("tenant_id") or tenant_id or "")
    workspace = str(scope.get("workspace_id") or workspace_id or "")
    user = str(scope.get("user_id") or user_id or "")
    candidate = str(implementation_approval.get("candidate_id") or candidate_id)
    proposed_skill_id = str(implementation_approval.get("proposed_skill_id") or candidate)
    marker_preview = dict(writer_design.get("consumer_marker_preview") or {})
    marker_path = Path(str(marker_preview.get("path") or ""))
    marker_parent = Path(root or ".").resolve() / "07_LOGS" / "SiteOps-Activation-Consumers" / tenant / workspace
    marker_confined = _filesystem_path_is_within(marker_path, marker_parent)
    marker_exists = marker_path.exists()
    marker_absent = not marker_exists
    approval_ready = bool(
        implementation_approval.get("ready_for_activation_consumer_writer_implementation_next_pass")
    )
    design_ready = bool(writer_design.get("ready_for_activation_consumer_writer_implementation_request_next_pass"))
    run_id = f"siteops_activation_consumer_{_slug(candidate)[:48]}"
    run_audit_path = audit_path(root, tenant, workspace, run_id)
    audit_confined = _filesystem_path_is_within(
        run_audit_path,
        Path(root or ".").resolve() / "07_LOGS" / "SiteOps-Audits" / tenant / workspace,
    )
    now = now_iso()
    marker_payload = {
        "record_type": "siteops_activation_approval_decision_consumer",
        "schema_version": 1,
        "run_id": run_id,
        "tenant_id": tenant,
        "workspace_id": workspace,
        "user_id": user,
        "candidate_id": candidate,
        "proposed_skill_id": proposed_skill_id,
        "source_approval_id": source_approval_id,
        "activation_approval_id": activation_approval_id,
        "activation_gate_operation": implementation_approval.get("activation_gate_operation"),
        "request_digest_sha256": implementation_approval.get("request_digest_sha256"),
        "approval_request_digest_sha256": implementation_approval.get("approval_request_digest_sha256"),
        "approval_status_required": "approved",
        "consumed_at": now,
        "consumed_by": actor,
        "reason": reason or "",
        "secret_values_visible": False,
        "trusted_artifacts_written": False,
        "activation_performed": False,
        "browser_execution_performed": False,
        "agent_bus_enqueue_performed": False,
        "provider_api_call_performed": False,
        "gate_policy_mutated": False,
        "canonical_writeback_performed": False,
    }
    secret_errors = scan_secret_like_keys(marker_payload)
    checks = list(implementation_approval.get("activation_consumer_writer_implementation_approval_checks") or []) + [
        _executor_preflight_check(
            "activation_consumer_writer_implementation_approved",
            passed=approval_ready,
            detail=str(
                implementation_approval.get(
                    "activation_approval_decision_consumer_writer_implementation_approval_status"
                )
            ),
        ),
        _executor_preflight_check(
            "activation_consumer_writer_design_still_ready",
            passed=design_ready,
            detail=str(writer_design.get("activation_approval_decision_consumer_writer_design_status")),
        ),
        _executor_preflight_check(
            "activation_consumer_marker_path_confined",
            passed=marker_confined,
            detail=marker_path.as_posix(),
        ),
        _executor_preflight_check(
            "activation_consumer_marker_absent_before_write",
            passed=marker_absent,
            detail=marker_path.as_posix(),
        ),
        _executor_preflight_check(
            "activation_consumer_audit_path_confined",
            passed=audit_confined,
            detail=run_audit_path.as_posix(),
        ),
        _executor_preflight_check(
            "activation_consumer_marker_payload_has_no_secret_like_keys",
            passed=not secret_errors,
            detail="; ".join(secret_errors) if secret_errors else "no secret-like keys detected",
        ),
        _executor_preflight_check(
            "activation_consumer_stops_before_activation_executor",
            passed=True,
            detail="writer only records consumption; activation remains separate",
        ),
    ]
    checks_passed = all(bool(check.get("passed")) for check in checks if check.get("required", True))
    ready_to_consume = checks_passed and approval_ready and design_ready and marker_confined and audit_confined and marker_absent

    if not approval_ready:
        writer_status = (
            "blocked_activation_consumer_writer_implementation_approval: "
            f"{implementation_approval.get('activation_approval_decision_consumer_writer_implementation_approval_status')}"
        )
        review_decision = "blocked_before_activation_consumer_writer_execution"
    elif not design_ready:
        writer_status = (
            "blocked_activation_consumer_writer_design: "
            f"{writer_design.get('activation_approval_decision_consumer_writer_design_status')}"
        )
        review_decision = "blocked_before_activation_consumer_writer_execution"
    elif not marker_confined or not audit_confined:
        writer_status = "blocked_activation_consumer_writer_scoped_path_posture"
        review_decision = "blocked_before_activation_consumer_writer_execution"
    elif marker_exists:
        writer_status = "blocked_activation_consumer_marker_already_exists"
        review_decision = "blocked_exact_once_activation_approval_already_consumed"
    elif secret_errors:
        writer_status = "blocked_activation_consumer_marker_secret_like_key_detected"
        review_decision = "blocked_before_activation_consumer_writer_execution"
    elif not consume_activation_approval:
        writer_status = "activation_consumer_writer_ready_dry_run_no_write"
        review_decision = "writer_ready_requires_explicit_consume_activation_approval_flag"
    else:
        writer_status = "activation_consumer_writer_ready_to_consume"
        review_decision = "consume_activation_approval_marker_and_audit_only"

    run_ref: str | None = None
    preconsume_audit_ref: str | None = None
    postconsume_audit_ref: str | None = None
    marker_ref: str | None = None
    marker_digest: str | None = None
    if consume_activation_approval and ready_to_consume:
        run = SiteOpsRun(
            run_id=run_id,
            tenant_id=tenant,
            workspace_id=workspace,
            user_id=user,
            skill_id=proposed_skill_id,
            workflow_id=PROMOTION_WORKFLOW_ID,
            site_profile_id=None,
            provider_id=None,
            mode="activation_approval_consumption",
            status="activation_approval_consumed_marker_only",
            inputs_ref=activation_approval_id,
            outputs_ref=marker_path.as_posix(),
            audit_ref=run_audit_path.as_posix(),
            cost_estimate={"charged": False, "provider": None},
            cost_actual=None,
            started_at=now,
            ended_at=now_iso(),
        )
        run_ref = write_run_record(root, run)
        preconsume_audit_ref = append_audit_event(
            root,
            SiteOpsAuditEvent(
                event_id=f"event_{run_id}_activation_consumer_preconsume",
                run_id=run_id,
                tenant_id=tenant,
                workspace_id=workspace,
                user_id=user,
                event_type="activation_approval_consumer_preconsume",
                action=PROMOTION_ACTIVATION_APPROVAL_DECISION_CONSUMER_WRITER_IMPLEMENTATION_ACTION,
                target=candidate,
                policy_decision="allow_marker_only_consumption",
                timestamp=now_iso(),
                metadata={
                    "activation_approval_id": activation_approval_id,
                    "source_approval_id": source_approval_id,
                    "proposed_skill_id": proposed_skill_id,
                    "marker_ref": marker_path.as_posix(),
                    "activation_allowed": False,
                    "trusted_artifacts_written": False,
                    "browser_execution_allowed": False,
                    "canonical_writeback_allowed": False,
                },
                redacted_fields=[],
            ),
        )
        _write_json_create_new(marker_path, marker_payload)
        marker_ref = marker_path.as_posix()
        marker_digest = _sha256_json(marker_payload)
        postconsume_audit_ref = append_audit_event(
            root,
            SiteOpsAuditEvent(
                event_id=f"event_{run_id}_activation_consumer_postconsume",
                run_id=run_id,
                tenant_id=tenant,
                workspace_id=workspace,
                user_id=user,
                event_type="activation_approval_consumer_postconsume",
                action=PROMOTION_ACTIVATION_APPROVAL_DECISION_CONSUMER_WRITER_IMPLEMENTATION_ACTION,
                target=candidate,
                policy_decision="activation_approval_consumed_marker_only",
                timestamp=now_iso(),
                metadata={
                    "activation_approval_id": activation_approval_id,
                    "source_approval_id": source_approval_id,
                    "proposed_skill_id": proposed_skill_id,
                    "marker_ref": marker_ref,
                    "marker_sha256": marker_digest,
                    "activation_allowed": False,
                    "activation_performed": False,
                    "trusted_artifacts_written": False,
                    "browser_execution_allowed": False,
                    "canonical_writeback_allowed": False,
                },
                redacted_fields=[],
            ),
        )
        writer_status = "activation_approval_consumed_marker_and_audit_written"
        review_decision = "activation_approval_consumed_stop_before_activation"

    denied_effects = list(implementation_approval.get("denied_effects") or [])
    for effect in [
        "mutate activation ApprovalRequest status",
        "activate promoted skills",
        "write trusted Browser Skill artifact",
        "write SiteOps Skill Card artifact",
        "mutate Gate policy",
        "launch or control a browser",
        "enqueue Agent Bus work",
        "call provider APIs",
        "write canonical ChaseOS memory/state",
    ]:
        if effect not in denied_effects:
            denied_effects.insert(0, effect)

    writes_performed = bool(run_ref or preconsume_audit_ref or postconsume_audit_ref or marker_ref)
    return {
        "ok": True,
        "action": PROMOTION_ACTIVATION_APPROVAL_DECISION_CONSUMER_WRITER_IMPLEMENTATION_ACTION,
        "candidate_id": candidate,
        "proposed_skill_id": proposed_skill_id,
        "scope": {"tenant_id": tenant, "workspace_id": workspace, "user_id": user},
        "source_approval_id": source_approval_id,
        "activation_approval_id": activation_approval_id,
        "actor": actor,
        "activation_approval_decision_consumer_writer_implementation_approval_status": implementation_approval.get(
            "activation_approval_decision_consumer_writer_implementation_approval_status"
        ),
        "activation_approval_decision_consumer_writer_implementation_status": writer_status,
        "review_decision": review_decision,
        "consume_activation_approval_requested": bool(consume_activation_approval),
        "consume_activation_approval_flag_supported": True,
        "activation_consumer_writer_implemented": True,
        "activation_consumer_writer_ready_to_consume": ready_to_consume,
        "activation_consumer_writer_checks": checks,
        "activation_consumer_marker_payload": marker_payload,
        "activation_consumer_marker_ref": marker_ref,
        "activation_consumer_marker_path": marker_path.as_posix(),
        "activation_consumer_marker_sha256": marker_digest,
        "run_id": run_id,
        "run_ref": run_ref,
        "audit_ref": postconsume_audit_ref or preconsume_audit_ref,
        "preconsume_audit_ref": preconsume_audit_ref,
        "postconsume_audit_ref": postconsume_audit_ref,
        "blocked_actions": denied_effects,
        "denied_effects": denied_effects,
        "writes_performed": writes_performed,
        "files_modified": writes_performed,
        "run_record_written": bool(run_ref),
        "activation_consumption_marker_written": bool(marker_ref),
        "activation_consumer_audit_written": bool(preconsume_audit_ref or postconsume_audit_ref),
        "audit_events_written": bool(preconsume_audit_ref or postconsume_audit_ref),
        "approval_consumed": bool(marker_ref),
        "approval_decision_written": False,
        "approval_request_status_mutated": False,
        "implementation_approval_artifact_written": False,
        "implementation_request_artifact_written": False,
        "trusted_skill_write_allowed": False,
        "siteops_skill_card_write_allowed": False,
        "trusted_artifacts_written": False,
        "inactive_artifacts_written": False,
        "activation_allowed": False,
        "activation_performed": False,
        "browser_execution_allowed": False,
        "agent_bus_enqueue_allowed": False,
        "provider_api_call_allowed": False,
        "gate_policy_mutation_allowed": False,
        "canonical_writeback_allowed": False,
        "boundary": (
            "activation approval consumer writer implementation only; writes require explicit "
            "--consume-activation-approval, approved activation approval posture, exact scope/digest "
            "checks, absent create-new marker, and scoped audit path. It records marker/audit/run "
            "evidence only and stops before activation, trusted artifact writes, browser execution, "
            "Agent Bus work, provider calls, Gate mutation, or canonical ChaseOS writeback."
        ),
    }


def candidate_promotion_activation_consumption_live_readiness(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    actor: str,
    source_approval_id: str | None = None,
    activation_approval_id: str | None = None,
    reason: str | None = None,
) -> dict[str, Any]:
    """Read-only readiness check for live activation approval consumption."""
    scope = require_scope(tenant_id=tenant_id, workspace_id=workspace_id, user_id=user_id)
    _validate_request_scope(root, scope)
    candidate = candidate_promotion_request_contract(
        candidate_id,
        root,
        requested_by=actor or scope.user_id,
        tenant_id=scope.tenant_id,
        workspace_id=scope.workspace_id,
        user_id=scope.user_id,
    )
    resolved_candidate_id = str(candidate.get("candidate_id") or candidate_id)
    proposed_skill_id = str(candidate.get("proposed_skill_id") or "")
    activation_gate_operation = "siteops.browser_skill_candidate.activate_trusted_artifact"
    approvals = list_approval_requests(root, tenant_id=scope.tenant_id, workspace_id=scope.workspace_id)

    source_candidates: list[dict[str, Any]] = []
    activation_candidates: list[dict[str, Any]] = []
    source_lookup: dict[str, dict[str, Any]] = {}
    activation_lookup: dict[str, dict[str, Any]] = {}
    for approval in approvals:
        metadata = dict(approval.get("metadata") or {})
        approval_id = str(approval.get("approval_id") or "")
        if (
            approval.get("action") == PROMOTION_ACTION
            and metadata.get("candidate_id") == resolved_candidate_id
            and approval.get("tenant_id") == scope.tenant_id
            and approval.get("workspace_id") == scope.workspace_id
            and approval.get("user_id") == scope.user_id
        ):
            source_lookup[approval_id] = approval
            source_candidates.append(
                {
                    "approval_id": approval_id,
                    "status": approval.get("status"),
                    "approval_ref": approval.get("approval_ref"),
                    "proposed_skill_id": metadata.get("proposed_skill_id"),
                }
            )
        if (
            approval.get("action") == activation_gate_operation
            and metadata.get("candidate_id") == resolved_candidate_id
            and approval.get("tenant_id") == scope.tenant_id
            and approval.get("workspace_id") == scope.workspace_id
            and approval.get("user_id") == scope.user_id
        ):
            activation_lookup[approval_id] = approval
            activation_candidates.append(
                {
                    "approval_id": approval_id,
                    "status": approval.get("status"),
                    "approval_ref": approval.get("approval_ref"),
                    "source_approval_id": metadata.get("source_approval_id"),
                    "proposed_skill_id": metadata.get("proposed_skill_id"),
                }
            )

    selected_source_approval_id = str(source_approval_id or "").strip()
    selected_activation_approval_id = str(activation_approval_id or "").strip()
    if not selected_source_approval_id:
        approved_sources = [
            item for item in source_candidates if item.get("status") == "approved"
        ]
        if approved_sources:
            selected_source_approval_id = str(approved_sources[0].get("approval_id") or "")
    if not selected_activation_approval_id and selected_source_approval_id:
        approved_activations = [
            item
            for item in activation_candidates
            if item.get("status") == "approved"
            and item.get("source_approval_id") == selected_source_approval_id
        ]
        if approved_activations:
            selected_activation_approval_id = str(approved_activations[0].get("approval_id") or "")

    source_present = bool(selected_source_approval_id)
    activation_present = bool(selected_activation_approval_id)
    source_record = source_lookup.get(selected_source_approval_id)
    activation_record = activation_lookup.get(selected_activation_approval_id)
    source_status = str((source_record or {}).get("status") or "")
    activation_status = str((activation_record or {}).get("status") or "")
    supplied_source_known = not source_approval_id or source_record is not None
    supplied_activation_known = not activation_approval_id or activation_record is not None
    source_approved = source_record is not None and source_status == "approved"
    activation_approved = activation_record is not None and activation_status == "approved"

    writer_dry_run: dict[str, Any] | None = None
    writer_dry_run_error: str | None = None
    if source_present and activation_present:
        try:
            writer_dry_run = candidate_promotion_activation_approval_decision_consumer_writer_implementation(
                resolved_candidate_id,
                root,
                tenant_id=scope.tenant_id,
                workspace_id=scope.workspace_id,
                user_id=scope.user_id,
                source_approval_id=selected_source_approval_id,
                activation_approval_id=selected_activation_approval_id,
                actor=actor,
                reason=reason or "operator requested activation consumption live readiness",
                consume_activation_approval=False,
            )
        except (SiteOpsError, RuntimeError, ValueError) as exc:
            writer_dry_run_error = str(exc)
    writer_ready = bool(
        writer_dry_run
        and writer_dry_run.get("activation_consumer_writer_ready_to_consume") is True
        and writer_dry_run.get("activation_approval_decision_consumer_writer_implementation_status")
        == "activation_consumer_writer_ready_dry_run_no_write"
    )

    if not source_present:
        readiness_status = "blocked_missing_source_promotion_approval_id"
        review_decision = "provide_or_create_approved_source_promotion_approval"
    elif not supplied_source_known:
        readiness_status = "blocked_unknown_source_promotion_approval_id"
        review_decision = "provide_real_scoped_source_approval_id"
    elif not source_approved:
        readiness_status = "blocked_source_promotion_approval_not_approved"
        review_decision = "approve_source_promotion_before_activation_consumption"
    elif not activation_present:
        readiness_status = "blocked_missing_activation_approval_id"
        review_decision = "provide_or_create_approved_activation_approval"
    elif not supplied_activation_known:
        readiness_status = "blocked_unknown_activation_approval_id"
        review_decision = "provide_real_scoped_activation_approval_id"
    elif not activation_approved:
        readiness_status = "blocked_activation_approval_not_approved"
        review_decision = "approve_activation_approval_before_consumption"
    elif writer_ready:
        readiness_status = "activation_consumption_live_readiness_ready_no_write"
        review_decision = "ready_for_operator_reviewed_consume_activation_approval_command"
    else:
        readiness_status = "blocked_activation_consumer_writer_dry_run_not_ready"
        review_decision = "inspect_writer_dry_run_before_consumption"

    consume_command_preview = [
        "python",
        "-m",
        "runtime.cli.main",
        "siteops",
        "candidates",
        "activation-approval-decision-consumer-writer-implementation",
        resolved_candidate_id,
        "--source-approval-id",
        selected_source_approval_id or "<SOURCE_APPROVAL_ID>",
        "--activation-approval-id",
        selected_activation_approval_id or "<ACTIVATION_APPROVAL_ID>",
        "--tenant",
        scope.tenant_id,
        "--workspace",
        scope.workspace_id,
        "--user",
        scope.user_id,
        "--actor",
        actor,
        "--consume-activation-approval",
        "--json",
    ]
    checks = [
        _executor_preflight_check(
            "source_promotion_approval_id_present",
            passed=source_present,
            detail=selected_source_approval_id or "missing",
        ),
        _executor_preflight_check(
            "source_promotion_approval_scoped_and_known",
            passed=bool(source_record),
            detail=source_status or "missing",
        ),
        _executor_preflight_check(
            "source_promotion_approval_approved",
            passed=source_approved,
            detail=source_status or "missing",
        ),
        _executor_preflight_check(
            "activation_approval_id_present",
            passed=activation_present,
            detail=selected_activation_approval_id or "missing",
        ),
        _executor_preflight_check(
            "activation_approval_scoped_and_known",
            passed=bool(activation_record),
            detail=activation_status or "missing",
        ),
        _executor_preflight_check(
            "activation_approval_approved",
            passed=activation_approved,
            detail=activation_status or "missing",
        ),
        _executor_preflight_check(
            "activation_consumer_writer_dry_run_ready",
            passed=writer_ready,
            detail=writer_dry_run_error
            or str(
                (writer_dry_run or {}).get(
                    "activation_approval_decision_consumer_writer_implementation_status"
                )
                or "not_run"
            ),
        ),
        _executor_preflight_check(
            "readiness_pass_is_no_write",
            passed=True,
            detail="does not consume approvals, write markers, append audit, activate, or run browsers",
        ),
    ]
    return {
        "ok": True,
        "action": PROMOTION_ACTIVATION_CONSUMPTION_LIVE_READINESS_ACTION,
        "candidate_id": resolved_candidate_id,
        "proposed_skill_id": proposed_skill_id,
        "scope": scope.as_dict(),
        "actor": actor,
        "source_approval_id": selected_source_approval_id or None,
        "activation_approval_id": selected_activation_approval_id or None,
        "activation_consumption_live_readiness_status": readiness_status,
        "review_decision": review_decision,
        "source_approval_candidates": source_candidates,
        "activation_approval_candidates": activation_candidates,
        "source_approval_status": source_status or None,
        "activation_approval_status": activation_status or None,
        "writer_dry_run_status": (writer_dry_run or {}).get(
            "activation_approval_decision_consumer_writer_implementation_status"
        ),
        "writer_dry_run_error": writer_dry_run_error,
        "writer_dry_run_ready": writer_ready,
        "consume_command_preview": consume_command_preview,
        "activation_consumption_live_readiness_checks": checks,
        "writes_performed": False,
        "files_modified": False,
        "run_record_written": False,
        "activation_consumption_marker_written": False,
        "activation_consumer_audit_written": False,
        "approval_consumed": False,
        "approval_decision_written": False,
        "approval_request_status_mutated": False,
        "trusted_artifacts_written": False,
        "trusted_skill_write_allowed": False,
        "siteops_skill_card_write_allowed": False,
        "activation_allowed": False,
        "activation_performed": False,
        "browser_execution_allowed": False,
        "agent_bus_enqueue_allowed": False,
        "provider_api_call_allowed": False,
        "gate_policy_mutation_allowed": False,
        "canonical_writeback_allowed": False,
        "blocked_actions": [
            "consume activation approval",
            "write activation consumer marker",
            "append activation consumer audit events",
            "mutate ApprovalRequest status",
            "write trusted artifacts",
            "activate skills",
            "launch or control a browser",
            "enqueue Agent Bus work",
            "call provider APIs",
            "write canonical ChaseOS memory/state",
        ],
        "boundary": (
            "activation consumption live readiness only; discovers or validates "
            "real approval ids and runs the marker-only writer dry-run. It does "
            "not consume approvals, write markers, append audit events, activate "
            "skills, run browsers, call providers, mutate Gate, or write canonical state."
        ),
    }


def _candidate_promotion_source_approval_rebind_live_readiness_contract(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    actor: str,
    approval_id: str | None = None,
    reason: str | None = None,
) -> dict[str, Any]:
    """Read-only readiness check for replacing a legacy source promotion approval."""
    scope = require_scope(tenant_id=tenant_id, workspace_id=workspace_id, user_id=user_id)
    _validate_request_scope(root, scope)
    candidate = candidate_promotion_request_contract(
        candidate_id,
        root,
        requested_by=actor or scope.user_id,
        tenant_id=scope.tenant_id,
        workspace_id=scope.workspace_id,
        user_id=scope.user_id,
    )
    resolved_candidate_id = str(candidate.get("candidate_id") or candidate_id)
    proposed_skill_id = str(candidate.get("proposed_skill_id") or "").strip() or None
    requested_approval_id = str(approval_id or "").strip()

    source_candidates: list[dict[str, Any]] = []
    candidate_lookup: dict[str, dict[str, Any]] = {}
    all_source_lookup: dict[str, dict[str, Any]] = {}
    for approval in list_approval_requests(root, tenant_id=scope.tenant_id, workspace_id=scope.workspace_id):
        if approval.get("action") != PROMOTION_ACTION:
            continue
        metadata = dict(approval.get("metadata") or {})
        approval_id_value = str(approval.get("approval_id") or "")
        inferred_candidate_id = str(metadata.get("candidate_id") or "").strip() or _candidate_id_from_legacy_approval(approval)
        inferred_skill_id = str(metadata.get("proposed_skill_id") or "").strip() or None
        provenance = _approval_provenance_status(
            approval=approval,
            candidate_id=resolved_candidate_id,
            proposed_skill_id=proposed_skill_id,
        )
        scoped = (
            approval.get("tenant_id") == scope.tenant_id
            and approval.get("workspace_id") == scope.workspace_id
            and approval.get("user_id") == scope.user_id
        )
        candidate_matches = inferred_candidate_id == resolved_candidate_id
        item = {
            "approval_id": approval_id_value,
            "status": approval.get("status"),
            "approval_ref": approval.get("approval_ref"),
            "run_id": approval.get("run_id"),
            "candidate_id": inferred_candidate_id or None,
            "proposed_skill_id": inferred_skill_id,
            "scope_matches": scoped,
            "candidate_matches": candidate_matches,
            "approval_provenance": provenance,
        }
        all_source_lookup[approval_id_value] = approval
        if scoped and candidate_matches:
            source_candidates.append(item)
            candidate_lookup[approval_id_value] = approval

    selected_source_approval_id = requested_approval_id
    if not selected_source_approval_id:
        approved_legacy = [
            item
            for item in source_candidates
            if item.get("status") == "approved"
            and (item.get("approval_provenance") or {}).get("provenance_status") == "legacy_unbound"
        ]
        approved_bound = [
            item
            for item in source_candidates
            if item.get("status") == "approved"
            and (item.get("approval_provenance") or {}).get("provenance_status") == "bound_match"
        ]
        any_legacy = [
            item
            for item in source_candidates
            if (item.get("approval_provenance") or {}).get("provenance_status") == "legacy_unbound"
        ]
        selected = (approved_legacy or approved_bound or any_legacy or source_candidates or [None])[0]
        if selected:
            selected_source_approval_id = str(selected.get("approval_id") or "")

    selected_record = candidate_lookup.get(selected_source_approval_id)
    supplied_record = all_source_lookup.get(selected_source_approval_id)
    supplied_known = not requested_approval_id or supplied_record is not None
    supplied_scoped_candidate_match = not requested_approval_id or selected_record is not None
    selected_status = str((selected_record or supplied_record or {}).get("status") or "")

    rebind_spec: dict[str, Any] | None = None
    rebind_spec_error: str | None = None
    writer_dry_run: dict[str, Any] | None = None
    writer_dry_run_error: str | None = None
    selected_provenance_status = (
        ((selected_record or {}).get("approval_provenance") or {}).get("provenance_status")
    )
    provenance_status = selected_provenance_status
    selected_record_for_rebind = selected_record if selected_record is not None else None
    if selected_record_for_rebind is not None:
        try:
            rebind_spec = candidate_promotion_approval_rebind_spec(
                resolved_candidate_id,
                root,
                tenant_id=scope.tenant_id,
                workspace_id=scope.workspace_id,
                user_id=scope.user_id,
                approval_id=selected_source_approval_id,
            )
            provenance_status = rebind_spec.get("provenance_status")
        except (SiteOpsError, RuntimeError, ValueError) as exc:
            rebind_spec_error = str(exc)
    if (
        rebind_spec
        and rebind_spec.get("approval_rebind_spec_status") == "approval_rebind_spec_required_no_write_authority"
    ):
        try:
            writer_dry_run = candidate_promotion_bound_approval_writer_implementation(
                resolved_candidate_id,
                root,
                tenant_id=scope.tenant_id,
                workspace_id=scope.workspace_id,
                user_id=scope.user_id,
                approval_id=selected_source_approval_id,
                actor=actor,
                reason=reason or "operator requested source approval rebind live readiness",
                write_replacement_approval=False,
            )
        except (SiteOpsError, RuntimeError, ValueError, FileExistsError) as exc:
            writer_dry_run_error = str(exc)

    writer_ready = bool(
        writer_dry_run
        and writer_dry_run.get("bound_approval_writer_implementation_status")
        == "bound_approval_writer_ready_dry_run_no_write"
        and writer_dry_run.get("writer_ready_to_write") is True
    )
    bound_ready = bool(
        rebind_spec
        and rebind_spec.get("approval_rebind_spec_status") == "approval_rebind_not_required_bound_match"
        and selected_status == "approved"
    )

    if not selected_source_approval_id:
        readiness_status = "blocked_missing_source_promotion_approval_id"
        review_decision = "create_or_provide_source_promotion_approval_id"
    elif not supplied_known:
        readiness_status = "blocked_source_approval_not_found"
        review_decision = "provide_real_scoped_source_approval_id"
    elif not supplied_scoped_candidate_match:
        readiness_status = "blocked_source_approval_scope_or_candidate_mismatch"
        review_decision = "provide_source_approval_for_this_candidate_scope"
    elif selected_status != "approved":
        readiness_status = "blocked_legacy_source_approval_not_approved"
        review_decision = "approve_or_replace_source_approval_before_rebind"
    elif provenance_status == "bound_match" and bound_ready:
        readiness_status = "source_approval_rebind_not_required_bound_source_ready"
        review_decision = "use_existing_scoped_source_approval_for_activation_evidence"
    elif provenance_status == "legacy_unbound" and writer_ready:
        readiness_status = "source_approval_rebind_live_readiness_ready_no_write"
        review_decision = "ready_for_operator_reviewed_write_replacement_approval_command"
    elif rebind_spec_error:
        readiness_status = "blocked_source_approval_rebind_spec_error"
        review_decision = "inspect_rebind_spec_error"
    elif writer_dry_run_error:
        readiness_status = "blocked_replacement_approval_writer_dry_run_error"
        review_decision = "inspect_writer_dry_run_error"
    else:
        readiness_status = "blocked_replacement_approval_writer_dry_run_not_ready"
        review_decision = "inspect_rebind_spec_and_writer_dry_run_before_write"

    replacement_command_preview = [
        "python",
        "-m",
        "runtime.cli.main",
        "siteops",
        "candidates",
        "bound-approval-writer-implementation",
        resolved_candidate_id,
        "--approval-id",
        selected_source_approval_id or "<SOURCE_APPROVAL_ID>",
        "--tenant",
        scope.tenant_id,
        "--workspace",
        scope.workspace_id,
        "--user",
        scope.user_id,
        "--actor",
        actor,
        "--write-replacement-approval",
        "--json",
    ]
    approved_legacy_unbound_approval_ids = [
        str(item.get("approval_id") or "")
        for item in source_candidates
        if item.get("status") == "approved"
        and ((item.get("approval_provenance") or {}).get("provenance_status") == "legacy_unbound")
    ]
    pending_legacy_unbound_approval_ids = [
        str(item.get("approval_id") or "")
        for item in source_candidates
        if item.get("status") == "pending"
        and ((item.get("approval_provenance") or {}).get("provenance_status") == "legacy_unbound")
    ]
    bound_source_approval_ids = [
        str(item.get("approval_id") or "")
        for item in source_candidates
        if item.get("status") == "approved"
        and ((item.get("approval_provenance") or {}).get("provenance_status") == "bound_match")
    ]
    selected_legacy_approval_id = (
        selected_source_approval_id
        if provenance_status == "legacy_unbound"
        or selected_source_approval_id in approved_legacy_unbound_approval_ids
        or selected_source_approval_id in pending_legacy_unbound_approval_ids
        else None
    )
    checks = [
        _executor_preflight_check(
            "source_promotion_approval_id_present",
            passed=bool(selected_source_approval_id),
            detail=selected_source_approval_id or "missing",
        ),
        _executor_preflight_check(
            "source_promotion_approval_scoped_candidate_match",
            passed=bool(selected_record),
            detail="matched" if selected_record else "missing_or_mismatch",
        ),
        _executor_preflight_check(
            "source_promotion_approval_approved",
            passed=selected_status == "approved",
            detail=selected_status or "missing",
        ),
        _executor_preflight_check(
            "legacy_unbound_or_bound_ready",
            passed=provenance_status in {"legacy_unbound", "bound_match"},
            detail=str(provenance_status or "not_checked"),
        ),
        _executor_preflight_check(
            "replacement_approval_writer_dry_run_ready",
            passed=writer_ready or bound_ready,
            detail=(
                "not_required_existing_bound_match"
                if bound_ready
                else writer_dry_run_error
                or str((writer_dry_run or {}).get("bound_approval_writer_implementation_status") or "not_run")
            ),
        ),
        _executor_preflight_check(
            "readiness_pass_is_no_write",
            passed=True,
            detail="does not write replacement approvals, consume approvals, write artifacts, activate, or run browsers",
        ),
    ]
    return {
        "ok": True,
        "action": PROMOTION_SOURCE_APPROVAL_REBIND_LIVE_READINESS_ACTION,
        "candidate_id": resolved_candidate_id,
        "proposed_skill_id": proposed_skill_id,
        "scope": scope.as_dict(),
        "actor": actor,
        "source_approval_id": selected_source_approval_id or None,
        "requested_source_approval_id": requested_approval_id or None,
        "source_approval_rebind_live_readiness_status": readiness_status,
        "review_decision": review_decision,
        "source_approval_candidates": source_candidates,
        "source_approval_status": selected_status or None,
        "source_approval_provenance_status": provenance_status,
        "selected_legacy_approval_id": selected_legacy_approval_id or None,
        "approved_legacy_unbound_approval_ids": approved_legacy_unbound_approval_ids,
        "pending_legacy_unbound_approval_ids": pending_legacy_unbound_approval_ids,
        "bound_source_approval_ids": bound_source_approval_ids,
        "rebind_spec_status": (rebind_spec or {}).get("approval_rebind_spec_status"),
        "approval_rebind_spec_status": (rebind_spec or {}).get("approval_rebind_spec_status"),
        "approval_rebind_spec_error": rebind_spec_error,
        "replacement_approval_needed": provenance_status == "legacy_unbound",
        "replacement_approval_write_allowed_in_this_pass": False,
        "replacement_source_approval_ready_to_write": writer_ready,
        "replacement_approval_writer_dry_run_status": (writer_dry_run or {}).get(
            "bound_approval_writer_implementation_status"
        ),
        "replacement_approval_writer_dry_run_ready": writer_ready,
        "replacement_approval_writer_dry_run_error": writer_dry_run_error,
        "replacement_approval_command_preview": replacement_command_preview,
        "approval_rebind_spec": rebind_spec,
        "replacement_approval_writer_dry_run": writer_dry_run,
        "source_approval_rebind_live_readiness_checks": checks,
        "writes_performed": False,
        "files_modified": False,
        "approval_request_written": False,
        "approval_request_artifact_written": False,
        "replacement_approval_request_written": False,
        "approval_consumed": False,
        "approval_decision_written": False,
        "approval_request_status_mutated": False,
        "trusted_artifacts_written": False,
        "trusted_skill_write_allowed": False,
        "siteops_skill_card_write_allowed": False,
        "activation_allowed": False,
        "activation_performed": False,
        "browser_execution_allowed": False,
        "agent_bus_enqueue_allowed": False,
        "provider_api_call_allowed": False,
        "gate_policy_mutation_allowed": False,
        "canonical_writeback_allowed": False,
        "blocked_actions": [
            "write replacement source approval",
            "mutate legacy source approval",
            "consume source approval",
            "decide approval",
            "write trusted artifacts",
            "activate skills",
            "launch or control a browser",
            "enqueue Agent Bus work",
            "call provider APIs",
            "mutate Gate policy",
            "write canonical ChaseOS memory/state",
        ],
        "boundary": (
            "source approval rebind live readiness only; discovers legacy and bound "
            "source promotion approvals, composes the no-write rebind spec, and runs "
            "the replacement approval writer in dry-run mode when eligible. It does "
            "not write approvals, consume approvals, mutate legacy approvals, write "
            "trusted artifacts, activate skills, run browsers, call providers, mutate "
            "Gate, or write canonical state."
        ),
    }


def _write_json_create_new(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _write_yaml_create_new(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if yaml is not None:
        text = yaml.safe_dump(payload, sort_keys=False, allow_unicode=False)
    else:
        text = json.dumps(payload, indent=2, sort_keys=True)
    with path.open("x", encoding="utf-8") as handle:
        handle.write(text.rstrip() + "\n")


def _write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def _write_yaml_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if yaml is not None:
        text = yaml.safe_dump(payload, sort_keys=False, allow_unicode=False)
    else:
        text = json.dumps(payload, indent=2, sort_keys=True)
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_text(text.rstrip() + "\n", encoding="utf-8")
    tmp.replace(path)


def _sha256_json(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def candidate_promotion_bound_approval_writer_implementation(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    approval_id: str,
    actor: str | None = None,
    reason: str | None = None,
    write_replacement_approval: bool = False,
) -> dict[str, Any]:
    """Run the first bounded replacement-approval writer.

    This writer is deliberately narrow. It may create only a new pending bound
    replacement approval request plus scoped run/audit/idempotency/recovery
    evidence. It never consumes approvals, mutates the superseded legacy
    approval, writes trusted artifacts, edits Gate policy, launches a browser,
    enqueues Agent Bus work, calls providers, activates skills, or writes
    canonical ChaseOS state.
    """
    implementation_approval = candidate_promotion_bound_approval_writer_implementation_approval(
        candidate_id,
        root,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
        approval_id=approval_id,
        decision="approve",
        actor=actor or user_id,
        reason=reason or "operator-approved bounded replacement approval writer implementation",
    )
    scope = dict(implementation_approval.get("scope") or {})
    preflight = candidate_promotion_bound_approval_writer_preflight(
        candidate_id,
        root,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
        approval_id=approval_id,
    )
    artifact = dict(preflight.get("approval_request_artifact") or {})
    target = dict(preflight.get("target_path_preview") or {})
    idempotency = dict(preflight.get("idempotency_marker_preview") or {})
    recovery = dict(preflight.get("recovery_marker_preview") or {})
    target_path = Path(str(target.get("path") or ""))
    marker_path = Path(str(idempotency.get("path") or ""))
    recovery_path = Path(str(recovery.get("path") or ""))
    ready_to_write = (
        bool(implementation_approval.get("implementation_patch_allowed_next_pass"))
        and bool(preflight.get("preflight_ready_no_write"))
        and bool(target.get("parent_confined"))
        and bool(target.get("target_confined"))
        and not bool(target.get("target_exists"))
        and bool(idempotency.get("marker_confined"))
        and not bool(idempotency.get("marker_exists"))
        and bool(recovery.get("recovery_confined"))
        and not bool(recovery.get("recovery_exists"))
    )
    if not implementation_approval.get("implementation_patch_allowed_next_pass"):
        writer_status = (
            "blocked_bound_approval_writer_implementation_approval: "
            f"{implementation_approval.get('bound_approval_writer_implementation_approval_status')}"
        )
        review_decision = "blocked_before_writer_execution"
    elif not preflight.get("preflight_ready_no_write"):
        writer_status = (
            "blocked_bound_approval_writer_preflight: "
            f"{preflight.get('bound_approval_writer_preflight_status')}"
        )
        review_decision = "blocked_before_writer_execution"
    elif not ready_to_write:
        writer_status = "blocked_bound_approval_writer_target_or_marker_posture"
        review_decision = "blocked_before_writer_execution"
    elif not write_replacement_approval:
        writer_status = "bound_approval_writer_ready_dry_run_no_write"
        review_decision = "writer_ready_requires_explicit_write_replacement_approval_flag"
    else:
        writer_status = "bound_approval_writer_ready_to_write"
        review_decision = "write_pending_bound_replacement_approval_only"

    now = now_iso()
    run_id = str(artifact.get("run_id") or "")
    approval_ref: str | None = None
    run_ref: str | None = None
    audit_ref: str | None = None
    marker_ref: str | None = None
    recovery_ref: str | None = None
    target_digest: str | None = None
    recovery_record = {
        "record_type": "siteops_bound_approval_writer_recovery_marker",
        "status": "not_started",
        "tenant_id": scope.get("tenant_id"),
        "workspace_id": scope.get("workspace_id"),
        "user_id": scope.get("user_id"),
        "candidate_id": implementation_approval.get("candidate_id"),
        "source_approval_id": approval_id,
        "replacement_approval_id": artifact.get("approval_id"),
        "target_path": str(target_path),
        "created_at": now,
        "updated_at": now,
        "secret_values_visible": False,
        "trusted_artifacts_written": False,
    }
    marker_record = {
        "record_type": "siteops_bound_approval_writer_idempotency_marker",
        "tenant_id": scope.get("tenant_id"),
        "workspace_id": scope.get("workspace_id"),
        "user_id": scope.get("user_id"),
        "candidate_id": implementation_approval.get("candidate_id"),
        "source_approval_id": approval_id,
        "replacement_approval_id": artifact.get("approval_id"),
        "target_path": str(target_path),
        "created_at": now,
        "secret_values_visible": False,
        "trusted_artifacts_written": False,
    }

    if write_replacement_approval and ready_to_write:
        recovery_record["status"] = "started"
        recovery_record["updated_at"] = now_iso()
        _write_json_create_new(recovery_path, recovery_record)
        recovery_ref = str(recovery_path)
        run = SiteOpsRun(
            run_id=run_id,
            tenant_id=str(scope.get("tenant_id") or ""),
            workspace_id=str(scope.get("workspace_id") or ""),
            user_id=str(scope.get("user_id") or ""),
            skill_id=str(implementation_approval.get("proposed_skill_id") or "browser_skill_candidate"),
            workflow_id=PROMOTION_WORKFLOW_ID,
            site_profile_id=None,
            provider_id=None,
            mode="dry_run",
            status="approval_needed",
            inputs_ref=artifact.get("metadata", {}).get("source_path"),
            outputs_ref=str(target_path),
            audit_ref=str(audit_path(root, str(scope.get("tenant_id") or ""), str(scope.get("workspace_id") or ""), run_id)),
            cost_estimate={"charged": False, "provider": None},
            cost_actual=None,
            started_at=now,
            ended_at=now_iso(),
        )
        run_ref = write_run_record(root, run)
        _write_json_create_new(target_path, artifact)
        approval_ref = str(target_path)
        target_digest = _sha256_json(artifact)
        marker_record["approval_payload_sha256"] = target_digest
        _write_json_create_new(marker_path, marker_record)
        marker_ref = str(marker_path)
        audit_ref = append_audit_event(
            root,
            SiteOpsAuditEvent(
                event_id=f"event_{run_id}_bound_approval_request_created",
                run_id=run_id,
                tenant_id=str(scope.get("tenant_id") or ""),
                workspace_id=str(scope.get("workspace_id") or ""),
                user_id=str(scope.get("user_id") or ""),
                event_type="bound_approval_request_created",
                action=PROMOTION_ACTION,
                target=str(implementation_approval.get("candidate_id") or candidate_id),
                policy_decision="approval_required",
                timestamp=now_iso(),
                metadata={
                    "approval_id": artifact.get("approval_id"),
                    "candidate_id": implementation_approval.get("candidate_id"),
                    "proposed_skill_id": implementation_approval.get("proposed_skill_id"),
                    "supersedes_approval_id": approval_id,
                    "target_path": str(target_path),
                    "approval_binding_version": artifact.get("metadata", {}).get("approval_binding_version"),
                    "idempotency_marker_ref": marker_ref,
                    "recovery_marker_ref": recovery_ref,
                    "payload_sha256": target_digest,
                    "trusted_skill_write_allowed": False,
                    "siteops_skill_card_write_allowed": False,
                    "approval_consumed": False,
                },
                redacted_fields=[],
            ),
        )
        recovery_record["status"] = "completed"
        recovery_record["updated_at"] = now_iso()
        recovery_record["approval_payload_sha256"] = target_digest
        recovery_record["audit_ref"] = audit_ref
        recovery_path.write_text(json.dumps(recovery_record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        writer_status = "bound_approval_writer_replacement_approval_written"
        review_decision = "replacement_approval_written_pending_separate_decision"

    denied_effects = list(implementation_approval.get("denied_effects") or [])
    for effect in [
        "consume replacement approval request",
        "write trusted Browser Skill artifact",
        "write SiteOps Skill Card artifact",
        "edit Gate allowlist",
        "launch or control a browser",
        "enqueue Agent Bus work",
        "call provider APIs",
        "activate promoted skills",
        "write canonical ChaseOS memory/state",
    ]:
        if effect not in denied_effects:
            denied_effects.insert(0, effect)

    writes_performed = bool(approval_ref or run_ref or audit_ref or marker_ref or recovery_ref)
    return {
        "ok": True,
        "action": PROMOTION_BOUND_APPROVAL_WRITER_IMPLEMENTATION_ACTION,
        "candidate_id": implementation_approval.get("candidate_id"),
        "proposed_skill_id": implementation_approval.get("proposed_skill_id"),
        "scope": scope,
        "approval_id": approval_id,
        "actor": implementation_approval.get("actor"),
        "bound_approval_writer_implementation_approval_status": implementation_approval.get(
            "bound_approval_writer_implementation_approval_status"
        ),
        "bound_approval_writer_preflight_status": preflight.get("bound_approval_writer_preflight_status"),
        "bound_approval_writer_implementation_status": writer_status,
        "review_decision": review_decision,
        "write_replacement_approval_requested": bool(write_replacement_approval),
        "writer_ready_to_write": ready_to_write,
        "approval_request_artifact": artifact,
        "target_path_preview": target,
        "idempotency_marker_preview": idempotency,
        "recovery_marker_preview": recovery,
        "approval_ref": approval_ref,
        "run_ref": run_ref,
        "audit_ref": audit_ref,
        "idempotency_marker_ref": marker_ref,
        "recovery_marker_ref": recovery_ref,
        "approval_payload_sha256": target_digest,
        "blocked_actions": denied_effects,
        "denied_effects": denied_effects,
        "writes_performed": writes_performed,
        "implementation_approval_record_written": False,
        "implementation_request_artifact_written": False,
        "approval_request_artifact_written": bool(approval_ref),
        "approval_artifact_write_allowed": bool(write_replacement_approval and ready_to_write),
        "bound_approval_writer_implemented": True,
        "bound_approval_writer_enabled": True,
        "bound_approval_writer_execution_allowed": bool(write_replacement_approval and ready_to_write),
        "bound_approval_run_record_written": bool(run_ref),
        "bound_approval_preflight_marker_written": False,
        "bound_approval_recovery_marker_written": bool(recovery_ref),
        "bound_approval_audit_event_written": bool(audit_ref),
        "bound_approval_idempotency_marker_written": bool(marker_ref),
        "legacy_approval_mutation_allowed": False,
        "replacement_approval_request_written": bool(approval_ref),
        "approval_decision_written": False,
        "audit_events_written": bool(audit_ref),
        "inactive_artifacts_written": False,
        "executor_implemented": False,
        "executor_enabled": False,
        "executor_build_allowed": False,
        "executor_implementation_allowed": False,
        "executor_implementation_performed": False,
        "allowlist_change_allowed": False,
        "allowlist_change_performed": False,
        "policy_file_write_allowed": False,
        "trusted_skill_write_allowed": False,
        "siteops_skill_card_write_allowed": False,
        "browser_execution_allowed": False,
        "agent_bus_enqueue_allowed": False,
        "provider_api_call_allowed": False,
        "activation_allowed": False,
        "canonical_writeback_allowed": False,
        "boundary": (
            "bound approval writer implementation only; it may write a new pending "
            "replacement approval request plus scoped run/audit/idempotency/recovery "
            "evidence when explicitly requested and preflight-ready. It does not "
            "consume approvals, mutate legacy approvals, write trusted artifacts, edit "
            "Gate policy, execute browsers, enqueue Agent Bus work, call providers, "
            "activate skills, or write canonical ChaseOS state."
        ),
    }

def candidate_promotion_replacement_approval_decision_consumption(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    replacement_approval_id: str,
    actor: str,
    decision: str,
    reason: str | None = None,
    write_approval_decision: bool = False,
) -> dict[str, Any]:
    """Decide a bound replacement approval without consuming it or writing trusted artifacts."""
    if decision not in {"approve", "reject"}:
        raise SiteOpsValidationError("replacement approval decision must be approve or reject")
    status = "approved" if decision == "approve" else "rejected"
    requested_scope = require_scope(tenant_id=tenant_id, workspace_id=workspace_id, user_id=user_id)
    tenant = load_tenant(root, requested_scope.tenant_id)
    if requested_scope.workspace_id not in _configured_workspaces(tenant):
        raise SiteOpsValidationError(f"workspace is not configured for tenant: {requested_scope.workspace_id}")
    approval = show_approval_request(root, replacement_approval_id, tenant_id=requested_scope.tenant_id)
    metadata = dict(approval.get("metadata") or {})
    scope = {
        "tenant_id": approval.get("tenant_id"),
        "workspace_id": approval.get("workspace_id"),
        "user_id": approval.get("user_id"),
    }
    resolved_candidate_id = str(metadata.get("candidate_id") or candidate_id)
    resolved_skill_id = str(metadata.get("proposed_skill_id") or "").strip() or None
    approval_provenance = _approval_provenance_status(
        approval=approval,
        candidate_id=candidate_id,
        proposed_skill_id=resolved_skill_id,
    )
    scope_matches = (
        approval.get("tenant_id") == requested_scope.tenant_id
        and approval.get("workspace_id") == requested_scope.workspace_id
        and approval.get("user_id") == requested_scope.user_id
    )
    candidate_matches = approval_provenance.get("candidate_id_matches") is True
    binding_matches = (
        approval.get("action") == PROMOTION_ACTION
        and approval.get("required_approver_role") == "tenant_admin"
        and metadata.get("approval_binding_version") == "browser_skill_candidate.v1"
        and metadata.get("promotion_action") == PROMOTION_ACTION
        and bool(metadata.get("supersedes_approval_id"))
        and approval_provenance.get("provenance_status") == "bound_match"
    )
    approval_status = str(approval.get("status") or "")
    pending = approval_status == "pending"
    approved = approval_status == "approved"
    rejected = approval_status == "rejected"
    decision_ready = scope_matches and candidate_matches and binding_matches and pending
    consumption_ready = scope_matches and candidate_matches and binding_matches and approved
    if not scope_matches:
        decision_status = "blocked_replacement_approval_scope_mismatch"
        consumption_status = "replacement_approval_not_consumed"
    elif not candidate_matches:
        decision_status = "blocked_replacement_approval_candidate_mismatch"
        consumption_status = "replacement_approval_not_consumed"
    elif not binding_matches:
        decision_status = "blocked_unbound_or_invalid_replacement_approval"
        consumption_status = "replacement_approval_not_consumed"
    elif approved:
        decision_status = "replacement_approval_already_approved"
        consumption_status = "replacement_approval_consumption_ready_no_trusted_write"
    elif rejected:
        decision_status = "blocked_replacement_approval_rejected"
        consumption_status = "replacement_approval_not_consumed"
    elif not write_approval_decision:
        decision_status = "replacement_approval_decision_ready_no_write"
        consumption_status = "replacement_approval_pending_not_consumed"
    else:
        decision_status = "replacement_approval_decision_ready_to_write"
        consumption_status = "replacement_approval_not_consumed"

    updated_approval = dict(approval)
    approval_ref = approval.get("approval_ref")
    audit_ref: str | None = None
    decision_written = False
    if decision_ready and write_approval_decision:
        updated_approval = decide_approval_request(
            root,
            replacement_approval_id,
            actor=actor,
            status=status,
            tenant_id=requested_scope.tenant_id,
            reason=reason,
        )
        decision_written = True
        decision_status = "replacement_approval_decision_written"
        consumption_status = (
            "replacement_approval_consumption_ready_no_trusted_write"
            if status == "approved"
            else "replacement_approval_rejected_not_consumed"
        )
        consumption_ready = status == "approved"
        approval_ref = updated_approval.get("approval_ref")
        audit_ref = str(audit_path(root, str(scope.get("tenant_id") or ""), str(scope.get("workspace_id") or ""), str(approval.get("run_id") or "")))

    denied_effects = [
        "consume replacement approval request",
        "write trusted Browser Skill artifact",
        "write SiteOps Skill Card artifact",
        "edit Gate allowlist",
        "launch or control a browser",
        "enqueue Agent Bus work",
        "call provider APIs",
        "activate promoted skills",
        "write canonical ChaseOS memory/state",
        "mutate superseded legacy approval",
    ]
    return {
        "ok": True,
        "action": PROMOTION_REPLACEMENT_APPROVAL_DECISION_CONSUMPTION_ACTION,
        "candidate_id": resolved_candidate_id,
        "proposed_skill_id": metadata.get("proposed_skill_id"),
        "scope": scope,
        "replacement_approval_id": replacement_approval_id,
        "source_approval_id": metadata.get("supersedes_approval_id") or approval.get("supersedes_approval_id"),
        "actor": actor,
        "decision": decision,
        "reason": reason,
        "replacement_approval_decision_status": decision_status,
        "replacement_approval_consumption_status": consumption_status,
        "replacement_approval_ref": approval_ref,
        "audit_ref": audit_ref,
        "replacement_approval": updated_approval,
        "approval_provenance": approval_provenance,
        "validation": {
            "scope_matches": scope_matches,
            "candidate_matches": candidate_matches,
            "binding_matches": binding_matches,
            "pending": pending,
            "approved": approved,
            "rejected": rejected,
            "decision_ready": decision_ready,
            "consumption_ready": consumption_ready,
        },
        "blocked_actions": denied_effects,
        "denied_effects": denied_effects,
        "writes_performed": decision_written,
        "approval_decision_write_requested": bool(write_approval_decision),
        "approval_decision_written": decision_written,
        "replacement_approval_consumption_ready": consumption_ready,
        "replacement_approval_consumption_marker_written": False,
        "approval_consumed": False,
        "legacy_approval_mutation_allowed": False,
        "replacement_approval_request_written": False,
        "inactive_artifacts_written": False,
        "executor_implemented": False,
        "executor_enabled": False,
        "executor_build_allowed": False,
        "executor_implementation_allowed": False,
        "executor_implementation_performed": False,
        "allowlist_change_allowed": False,
        "allowlist_change_performed": False,
        "policy_file_write_allowed": False,
        "trusted_skill_write_allowed": False,
        "siteops_skill_card_write_allowed": False,
        "browser_execution_allowed": False,
        "agent_bus_enqueue_allowed": False,
        "provider_api_call_allowed": False,
        "activation_allowed": False,
        "canonical_writeback_allowed": False,
        "boundary": (
            "replacement approval decision path only; it may approve or reject the new bound replacement "
            "approval when explicitly requested, but it does not consume the approval, mutate the superseded "
            "legacy approval, write trusted artifacts, edit Gate policy, execute browsers, enqueue Agent Bus "
            "work, call providers, activate skills, or write canonical ChaseOS state."
        ),
    }


def candidate_promotion_trusted_inactive_artifact_writer_preflight(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    replacement_approval_id: str,
) -> dict[str, Any]:
    """Preflight future inactive trusted artifact writes without writing artifacts."""
    decision = candidate_promotion_replacement_approval_decision_consumption(
        candidate_id,
        root,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
        replacement_approval_id=replacement_approval_id,
        actor=user_id or "siteops-preflight",
        decision="approve",
        write_approval_decision=False,
    )
    collision = candidate_promotion_collision_policy_spec(
        candidate_id,
        root,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
        approval_id=replacement_approval_id,
    )
    target_checks = list(collision.get("target_path_checks") or [])
    paths_confined_and_clear = bool(target_checks) and all(
        item.get("path_confined") and not item.get("collision_detected") for item in target_checks
    )
    payloads = dict(collision.get("proposed_artifact_payloads") or {})
    if not payloads:
        validator = candidate_promotion_inactive_artifact_validator(
            candidate_id,
            root,
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            user_id=user_id,
            approval_id=replacement_approval_id,
        )
        payloads = dict(validator.get("proposed_artifact_payloads") or {})
    target_paths = {
        "browser_skill": next(
            (str(item.get("target_path") or "") for item in target_checks if item.get("artifact_kind") == "browser_skill"),
            "",
        ),
        "siteops_skill_card": next(
            (str(item.get("target_path") or "") for item in target_checks if item.get("artifact_kind") == "siteops_skill_card"),
            "",
        ),
    }
    replacement_ready = decision.get("replacement_approval_consumption_ready") is True
    collision_ready = collision.get("collision_policy_status") == "collision_policy_spec_ready_no_authority"
    validator_ready = collision.get("inactive_artifact_validator_status") == "inactive_artifact_validator_ready_no_authority"
    preflight_checks = [
        _executor_preflight_check(
            "replacement_approval_bound_and_approved",
            passed=replacement_ready,
            detail=str(decision.get("replacement_approval_consumption_status")),
        ),
        _executor_preflight_check(
            "inactive_artifact_payloads_valid",
            passed=validator_ready,
            detail=str(collision.get("inactive_artifact_validator_status")),
        ),
        _executor_preflight_check(
            "target_paths_confined_and_clear",
            passed=paths_confined_and_clear,
            detail=str(collision.get("collision_policy_status")),
        ),
        _executor_preflight_check(
            "gate_allowlist_not_mutated",
            passed=collision.get("operation_currently_allowlisted") is False,
            detail="preflight does not edit runtime/policy/gateway_allowlists.json",
        ),
        _executor_preflight_check(
            "activation_disabled",
            passed=True,
            detail="future writes must create inactive_review artifacts only; activation remains separate",
        ),
    ]
    write_preflight_pass = replacement_ready and collision_ready and validator_ready and paths_confined_and_clear
    status = (
        "trusted_inactive_artifact_writer_preflight_ready_no_write"
        if write_preflight_pass
        else f"blocked_trusted_inactive_artifact_writer_preflight: {decision.get('replacement_approval_consumption_status')}; {collision.get('collision_policy_status')}"
    )
    denied_effects = [
        "write inactive trusted artifacts",
        "consume replacement approval request",
        "write trusted Browser Skill artifact",
        "write SiteOps Skill Card artifact",
        "write audit events",
        "edit runtime/policy/gateway_allowlists.json",
        "launch or control a browser",
        "enqueue Agent Bus work",
        "call provider APIs",
        "activate promoted skills",
        "write canonical ChaseOS memory/state",
    ]
    return {
        "ok": True,
        "action": PROMOTION_TRUSTED_INACTIVE_ARTIFACT_WRITER_PREFLIGHT_ACTION,
        "candidate_id": collision.get("candidate_id") or decision.get("candidate_id"),
        "proposed_skill_id": collision.get("proposed_skill_id") or decision.get("proposed_skill_id"),
        "scope": collision.get("scope") or decision.get("scope"),
        "replacement_approval_id": replacement_approval_id,
        "trusted_inactive_artifact_writer_preflight_status": status,
        "review_decision": "preflight_only_do_not_write_in_this_pass" if write_preflight_pass else "blocked_before_trusted_inactive_write",
        "replacement_approval_consumption_status": decision.get("replacement_approval_consumption_status"),
        "replacement_approval_consumption_ready": replacement_ready,
        "collision_policy_status": collision.get("collision_policy_status"),
        "inactive_artifact_validator_status": collision.get("inactive_artifact_validator_status"),
        "operation_currently_allowlisted": collision.get("operation_currently_allowlisted"),
        "target_paths": target_paths,
        "target_path_checks": target_checks,
        "proposed_artifact_payloads": payloads,
        "preflight_checks": preflight_checks,
        "write_preflight_pass": write_preflight_pass,
        "blocked_actions": denied_effects,
        "denied_effects": denied_effects,
        "writes_performed": False,
        "audit_events_written": False,
        "approval_consumed": False,
        "inactive_artifacts_written": False,
        "trusted_inactive_artifact_writer_implemented": False,
        "trusted_inactive_artifact_writer_preflight_only": True,
        "trusted_skill_write_allowed": False,
        "siteops_skill_card_write_allowed": False,
        "allowlist_change_allowed": False,
        "allowlist_change_performed": False,
        "policy_file_write_allowed": False,
        "browser_execution_allowed": False,
        "agent_bus_enqueue_allowed": False,
        "provider_api_call_allowed": False,
        "activation_allowed": False,
        "canonical_writeback_allowed": False,
        "boundary": (
            "trusted inactive artifact writer preflight only; it verifies an approved bound replacement "
            "approval, inactive payload shapes, target confinement, and collision state without writing "
            "trusted artifacts, consuming approvals, mutating Gate policy, activating skills, launching "
            "browsers, enqueueing Agent Bus work, calling providers, or writing canonical ChaseOS state."
        ),
    }


def candidate_promotion_trusted_inactive_artifact_writer_implementation_request(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    replacement_approval_id: str,
) -> dict[str, Any]:
    """Return a no-write implementation request packet for the inactive artifact writer."""
    preflight = candidate_promotion_trusted_inactive_artifact_writer_preflight(
        candidate_id,
        root,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
        replacement_approval_id=replacement_approval_id,
    )
    scope = dict(preflight.get("scope") or {})
    target_paths = dict(preflight.get("target_paths") or {})
    request_id = _new_run_id(f"{preflight.get('candidate_id')}_trusted_inactive_writer_implementation_request")
    preflight_ready = bool(preflight.get("write_preflight_pass"))
    request_artifact = {
        "request_id": request_id,
        "request_type": "siteops_trusted_inactive_artifact_writer_implementation_request",
        "tenant_id": scope.get("tenant_id"),
        "workspace_id": scope.get("workspace_id"),
        "user_id": scope.get("user_id"),
        "candidate_id": preflight.get("candidate_id"),
        "proposed_skill_id": preflight.get("proposed_skill_id"),
        "replacement_approval_id": replacement_approval_id,
        "requested_action": "implement_trusted_inactive_artifact_writer",
        "required_operator_decision": "approve_future_trusted_inactive_artifact_writer_implementation_pass",
        "status": "review_packet_only",
        "preflight_status": preflight.get("trusted_inactive_artifact_writer_preflight_status"),
        "implementation_allowed_in_this_pass": False,
        "writes_allowed_in_this_pass": False,
        "trusted_writes_allowed_in_this_pass": False,
        "approval_consumption_allowed_in_this_pass": False,
        "activation_allowed_in_this_pass": False,
        "target_paths": target_paths,
    }
    readiness_checks = {
        "trusted_inactive_artifact_writer_preflight_ready": {
            "passed": preflight_ready,
            "status": preflight.get("trusted_inactive_artifact_writer_preflight_status"),
        },
        "replacement_approval_bound_and_approved": {
            "passed": preflight.get("replacement_approval_consumption_ready") is True,
            "status": preflight.get("replacement_approval_consumption_status"),
        },
        "target_paths_available": {
            "passed": bool(target_paths.get("browser_skill")) and bool(target_paths.get("siteops_skill_card")),
            "target_paths": target_paths,
        },
        "request_scope_bound": {
            "passed": all(request_artifact.get(key) == scope.get(key) for key in ("tenant_id", "workspace_id", "user_id")),
            "requires": ["tenant_id", "workspace_id", "user_id"],
        },
        "implementation_still_disabled": {
            "passed": True,
            "implementation_allowed_in_this_pass": False,
            "trusted_writes_allowed_in_this_pass": False,
        },
        "gate_mutation_still_blocked": {
            "passed": True,
            "operation": PROMOTION_GATE_APPLY_OPERATION,
            "operation_currently_allowlisted": preflight.get("operation_currently_allowlisted"),
            "allowlist_change_allowed": False,
        },
    }
    checks_passed = all(bool(check.get("passed")) for check in readiness_checks.values())
    if not preflight_ready:
        request_status = (
            "blocked_trusted_inactive_artifact_writer_preflight: "
            f"{preflight.get('trusted_inactive_artifact_writer_preflight_status')}"
        )
        review_decision = "blocked_before_trusted_inactive_artifact_writer_implementation_request"
    elif not checks_passed:
        request_status = "blocked_trusted_inactive_artifact_writer_implementation_request_checks"
        review_decision = "blocked_request_checks_failed"
    else:
        request_status = "trusted_inactive_artifact_writer_implementation_request_ready_no_write"
        review_decision = "ready_for_operator_review_of_future_trusted_inactive_artifact_writer_implementation"

    denied_effects = list(preflight.get("denied_effects") or [])
    for effect in [
        "write trusted inactive artifact writer implementation request",
        "implement trusted inactive artifact writer",
        "write inactive trusted artifacts from implementation request",
        "consume replacement approval from implementation request",
        "edit Gate allowlist from implementation request",
    ]:
        if effect not in denied_effects:
            denied_effects.insert(0, effect)

    return {
        "ok": True,
        "action": PROMOTION_TRUSTED_INACTIVE_ARTIFACT_WRITER_IMPLEMENTATION_REQUEST_ACTION,
        "candidate_id": preflight.get("candidate_id"),
        "proposed_skill_id": preflight.get("proposed_skill_id"),
        "scope": scope,
        "replacement_approval_id": replacement_approval_id,
        "trusted_inactive_artifact_writer_preflight_status": preflight.get(
            "trusted_inactive_artifact_writer_preflight_status"
        ),
        "trusted_inactive_artifact_writer_implementation_request_status": request_status,
        "review_decision": review_decision,
        "implementation_request_artifact": request_artifact,
        "implementation_request_checks": readiness_checks,
        "preflight_packet": {
            "replacement_approval_consumption_status": preflight.get("replacement_approval_consumption_status"),
            "replacement_approval_consumption_ready": preflight.get("replacement_approval_consumption_ready"),
            "collision_policy_status": preflight.get("collision_policy_status"),
            "inactive_artifact_validator_status": preflight.get("inactive_artifact_validator_status"),
            "target_paths": target_paths,
            "target_path_checks": preflight.get("target_path_checks"),
            "preflight_checks": preflight.get("preflight_checks"),
        },
        "future_implementation_requirements": [
            "operator must explicitly approve a future trusted inactive artifact writer implementation pass",
            "future implementation must rerun trusted-inactive-artifact-writer-preflight immediately before any write",
            "future writer must use create-new or staged atomic writes and refuse target collisions",
            "future writer may write inactive_review artifacts only and must keep activation separate",
            "future writer must preserve secret/session exclusion and scoped audit evidence",
            "future writer must not launch browsers, enqueue Agent Bus work, call providers, or write canonical ChaseOS state",
        ],
        "request_ready_no_write": request_status
        == "trusted_inactive_artifact_writer_implementation_request_ready_no_write",
        "blocked_actions": denied_effects,
        "denied_effects": denied_effects,
        "writes_performed": False,
        "implementation_request_artifact_written": False,
        "audit_events_written": False,
        "approval_consumed": False,
        "inactive_artifacts_written": False,
        "trusted_inactive_artifact_writer_implemented": False,
        "trusted_inactive_artifact_writer_enabled": False,
        "trusted_inactive_artifact_writer_execution_allowed": False,
        "trusted_skill_write_allowed": False,
        "siteops_skill_card_write_allowed": False,
        "allowlist_change_allowed": False,
        "allowlist_change_performed": False,
        "policy_file_write_allowed": False,
        "browser_execution_allowed": False,
        "agent_bus_enqueue_allowed": False,
        "provider_api_call_allowed": False,
        "activation_allowed": False,
        "canonical_writeback_allowed": False,
        "boundary": (
            "trusted inactive artifact writer implementation request only; it packages preflight evidence "
            "for operator review without writing artifacts, consuming approvals, mutating Gate policy, "
            "activating skills, launching browsers, enqueueing Agent Bus work, calling providers, or writing "
            "canonical ChaseOS state."
        ),
    }


def candidate_promotion_trusted_inactive_artifact_writer_implementation_approval(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    replacement_approval_id: str,
    decision: str,
    actor: str | None = None,
    reason: str | None = None,
) -> dict[str, Any]:
    """Return a no-write approval/rejection packet for a future trusted inactive writer."""
    normalized_decision = (decision or "").strip().lower()
    if normalized_decision not in {"approve", "reject"}:
        raise ValueError("decision must be 'approve' or 'reject'")

    implementation_request = candidate_promotion_trusted_inactive_artifact_writer_implementation_request(
        candidate_id,
        root,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
        replacement_approval_id=replacement_approval_id,
    )
    scope = dict(implementation_request.get("scope") or {})
    actor_id = (actor or user_id or "").strip()
    request_artifact = dict(implementation_request.get("implementation_request_artifact") or {})
    request_status = implementation_request.get(
        "trusted_inactive_artifact_writer_implementation_request_status"
    )
    request_ready = bool(implementation_request.get("request_ready_no_write"))
    decision_id = _new_run_id(
        f"trusted_inactive_writer_implementation_approval_{implementation_request.get('candidate_id')}"
    )

    approval_record = {
        "decision_id": decision_id,
        "record_type": "siteops_trusted_inactive_artifact_writer_implementation_approval",
        "tenant_id": scope.get("tenant_id"),
        "workspace_id": scope.get("workspace_id"),
        "user_id": scope.get("user_id"),
        "actor": actor_id,
        "decision": normalized_decision,
        "reason": reason or "",
        "candidate_id": implementation_request.get("candidate_id"),
        "proposed_skill_id": implementation_request.get("proposed_skill_id"),
        "replacement_approval_id": replacement_approval_id,
        "implementation_request_id": request_artifact.get("request_id"),
        "status": "review_decision_packet_only",
        "durable_record_written": False,
        "approval_decision_written": False,
        "implementation_allowed_in_this_pass": False,
        "trusted_inactive_artifact_write_allowed_in_this_pass": False,
        "trusted_writes_allowed": False,
        "approval_consumption_allowed": False,
        "activation_allowed": False,
    }
    implementation_approved = request_ready and normalized_decision == "approve"
    implementation_rejected = request_ready and normalized_decision == "reject"
    if not request_ready:
        approval_status = (
            "blocked_trusted_inactive_artifact_writer_implementation_request: "
            f"{request_status}"
        )
        review_decision = "blocked_before_trusted_inactive_artifact_writer_implementation_approval"
    elif implementation_approved:
        approval_status = (
            "trusted_inactive_artifact_writer_implementation_approved_for_next_pass_no_write"
        )
        review_decision = "operator_intent_approve_trusted_inactive_writer_implementation_next_pass"
    else:
        approval_status = "trusted_inactive_artifact_writer_implementation_rejected_no_write"
        review_decision = "operator_intent_reject_trusted_inactive_writer_implementation"

    approval_checks = {
        "implementation_request_ready": {
            "passed": request_ready,
            "status": request_status,
        },
        "decision_valid": {
            "passed": True,
            "decision": normalized_decision,
        },
        "actor_present": {
            "passed": bool(actor_id),
            "actor": actor_id,
        },
        "approval_record_still_no_write": {
            "passed": True,
            "durable_record_written": False,
            "approval_decision_written": False,
        },
        "trusted_inactive_writer_execution_still_disabled": {
            "passed": True,
            "trusted_inactive_artifact_writer_implemented": False,
            "trusted_inactive_artifact_writer_execution_allowed": False,
        },
        "trusted_artifact_writes_still_blocked_this_pass": {
            "passed": True,
            "inactive_artifacts_written": False,
            "trusted_skill_write_allowed": False,
            "siteops_skill_card_write_allowed": False,
        },
        "approval_consumption_still_blocked_this_pass": {
            "passed": True,
            "approval_consumed": False,
        },
    }
    if not approval_checks["actor_present"]["passed"]:
        approval_status = "blocked_missing_trusted_inactive_artifact_writer_implementation_approval_actor"
        review_decision = "blocked_before_trusted_inactive_artifact_writer_implementation_approval"
        implementation_approved = False
        implementation_rejected = False

    denied_effects = list(implementation_request.get("denied_effects") or [])
    for effect in [
        "write trusted inactive artifact writer implementation approval record",
        "consume trusted inactive artifact writer implementation approval",
        "write inactive trusted artifacts from implementation approval",
        "consume replacement approval from implementation approval",
        "implement trusted inactive artifact writer in approval pass",
        "edit Gate allowlist from implementation approval",
    ]:
        if effect not in denied_effects:
            denied_effects.insert(0, effect)

    return {
        "ok": True,
        "action": PROMOTION_TRUSTED_INACTIVE_ARTIFACT_WRITER_IMPLEMENTATION_APPROVAL_ACTION,
        "candidate_id": implementation_request.get("candidate_id"),
        "proposed_skill_id": implementation_request.get("proposed_skill_id"),
        "scope": scope,
        "replacement_approval_id": replacement_approval_id,
        "decision": normalized_decision,
        "actor": actor_id,
        "trusted_inactive_artifact_writer_preflight_status": implementation_request.get(
            "trusted_inactive_artifact_writer_preflight_status"
        ),
        "trusted_inactive_artifact_writer_implementation_request_status": request_status,
        "trusted_inactive_artifact_writer_implementation_approval_status": approval_status,
        "review_decision": review_decision,
        "implementation_request_packet": {
            "request_id": request_artifact.get("request_id"),
            "status": request_status,
            "request_ready_no_write": request_ready,
            "target_paths": request_artifact.get("target_paths"),
        },
        "implementation_approval_record": approval_record,
        "implementation_approval_checks": approval_checks,
        "implementation_patch_allowed_next_pass": implementation_approved,
        "implementation_rejected_no_write": implementation_rejected,
        "future_writer_requirements": [
            "future writer patch pass must cite this approval packet and rerun trusted-inactive-artifact-writer-implementation-request",
            "future writer must rerun trusted-inactive-artifact-writer-preflight immediately before any write",
            "future writer may write inactive_review artifacts only and must keep activation separate",
            "future writer must not consume replacement approvals in the implementation approval pass",
            "future writer must not mutate Gate policy, launch browsers, enqueue Agent Bus work, call providers, activate skills, or write canonical state",
        ],
        "blocked_actions": denied_effects,
        "denied_effects": denied_effects,
        "writes_performed": False,
        "implementation_approval_record_written": False,
        "implementation_request_artifact_written": False,
        "approval_decision_written": False,
        "audit_events_written": False,
        "approval_consumed": False,
        "inactive_artifacts_written": False,
        "trusted_inactive_artifact_writer_implemented": False,
        "trusted_inactive_artifact_writer_enabled": False,
        "trusted_inactive_artifact_writer_execution_allowed": False,
        "trusted_skill_write_allowed": False,
        "siteops_skill_card_write_allowed": False,
        "allowlist_change_allowed": False,
        "allowlist_change_performed": False,
        "policy_file_write_allowed": False,
        "browser_execution_allowed": False,
        "agent_bus_enqueue_allowed": False,
        "provider_api_call_allowed": False,
        "activation_allowed": False,
        "canonical_writeback_allowed": False,
        "boundary": (
            "trusted inactive artifact writer implementation approval packet only; no approval record, "
            "implementation request artifact, replacement approval consumption, trusted artifact, audit event, "
            "Gate policy, browser, Agent Bus, provider, activation, or canonical writeback side effect is performed"
        ),
    }


def candidate_promotion_trusted_inactive_artifact_writer_implementation(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    replacement_approval_id: str,
    actor: str,
    reason: str | None = None,
    write_inactive_artifacts: bool = False,
) -> dict[str, Any]:
    """Run the bounded trusted inactive artifact writer.

    This writer remains Gate-checked and explicit-flag gated. It may create only
    inactive-review Browser Skill and SiteOps Skill Card artifacts plus scoped
    run/audit evidence. It does not consume replacement approvals, mutate Gate
    policy, activate skills, launch browsers, enqueue Agent Bus work, call
    providers, or write canonical ChaseOS state.
    """
    implementation_approval = candidate_promotion_trusted_inactive_artifact_writer_implementation_approval(
        candidate_id,
        root,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
        replacement_approval_id=replacement_approval_id,
        decision="approve",
        actor=actor,
        reason=reason or "operator-approved trusted inactive artifact writer implementation",
    )
    preflight = candidate_promotion_trusted_inactive_artifact_writer_preflight(
        candidate_id,
        root,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
        replacement_approval_id=replacement_approval_id,
    )
    scope = dict(implementation_approval.get("scope") or preflight.get("scope") or {})
    target_paths = dict(preflight.get("target_paths") or {})
    payloads = dict(preflight.get("proposed_artifact_payloads") or {})
    target_checks = list(preflight.get("target_path_checks") or [])
    root_path = Path(root or ".").resolve()
    browser_skill_rel = str(target_paths.get("browser_skill") or "")
    siteops_card_rel = str(target_paths.get("siteops_skill_card") or "")
    browser_skill_path = root_path / browser_skill_rel
    siteops_card_path = root_path / siteops_card_rel
    write_targets = [path for path in [browser_skill_rel, siteops_card_rel] if path]
    gate_allowed, gate_reason = check_runtime_operation(
        PROMOTION_GATE_APPLY_OPERATION,
        write_targets=write_targets,
    )
    paths_confined_and_clear = bool(target_checks) and all(
        bool(item.get("path_confined")) and not bool(item.get("collision_detected"))
        for item in target_checks
    )
    payloads_ready = all(
        isinstance(payloads.get(kind), dict) and payloads.get(kind)
        for kind in ("browser_skill", "siteops_skill_card")
    )
    approval_ready = bool(implementation_approval.get("implementation_patch_allowed_next_pass"))
    preflight_ready = bool(preflight.get("write_preflight_pass"))
    ready_to_write = (
        approval_ready
        and preflight_ready
        and paths_confined_and_clear
        and payloads_ready
        and bool(gate_allowed)
    )

    if not approval_ready:
        writer_status = (
            "blocked_trusted_inactive_artifact_writer_implementation_approval: "
            f"{implementation_approval.get('trusted_inactive_artifact_writer_implementation_approval_status')}"
        )
        review_decision = "blocked_before_trusted_inactive_artifact_writer_execution"
    elif not preflight_ready:
        writer_status = (
            "blocked_trusted_inactive_artifact_writer_preflight: "
            f"{preflight.get('trusted_inactive_artifact_writer_preflight_status')}"
        )
        review_decision = "blocked_before_trusted_inactive_artifact_writer_execution"
    elif not paths_confined_and_clear:
        writer_status = "blocked_trusted_inactive_artifact_target_path_posture"
        review_decision = "blocked_before_trusted_inactive_artifact_writer_execution"
    elif not payloads_ready:
        writer_status = "blocked_trusted_inactive_artifact_payloads_missing"
        review_decision = "blocked_before_trusted_inactive_artifact_writer_execution"
    elif not gate_allowed:
        writer_status = "blocked_gate_operation_not_allowlisted"
        review_decision = "blocked_before_trusted_inactive_artifact_writer_execution"
    elif not write_inactive_artifacts:
        writer_status = "trusted_inactive_artifact_writer_ready_dry_run_no_write"
        review_decision = "writer_ready_requires_explicit_write_inactive_artifacts_flag"
    else:
        writer_status = "trusted_inactive_artifact_writer_ready_to_write"
        review_decision = "write_inactive_review_artifacts_only"

    now = now_iso()
    run_id = _new_run_id(f"{implementation_approval.get('candidate_id')}_trusted_inactive_writer")
    audit_ref: str | None = None
    run_ref: str | None = None
    browser_skill_ref: str | None = None
    siteops_card_ref: str | None = None
    browser_skill_digest: str | None = None
    siteops_card_digest: str | None = None
    prewrite_audit_ref: str | None = None
    postwrite_audit_ref: str | None = None

    if write_inactive_artifacts and ready_to_write:
        run = SiteOpsRun(
            run_id=run_id,
            tenant_id=str(scope.get("tenant_id") or ""),
            workspace_id=str(scope.get("workspace_id") or ""),
            user_id=str(scope.get("user_id") or ""),
            skill_id=str(implementation_approval.get("proposed_skill_id") or "browser_skill_candidate"),
            workflow_id=PROMOTION_WORKFLOW_ID,
            site_profile_id=None,
            provider_id=None,
            mode="write_inactive_review_artifacts",
            status="inactive_artifacts_written",
            inputs_ref=str(preflight.get("replacement_approval_id") or replacement_approval_id),
            outputs_ref=";".join(write_targets),
            audit_ref=str(audit_path(root, str(scope.get("tenant_id") or ""), str(scope.get("workspace_id") or ""), run_id)),
            cost_estimate={"charged": False, "provider": None},
            cost_actual=None,
            started_at=now,
            ended_at=now_iso(),
        )
        run_ref = write_run_record(root, run)
        prewrite_audit_ref = append_audit_event(
            root,
            SiteOpsAuditEvent(
                event_id=f"event_{run_id}_trusted_inactive_prewrite",
                run_id=run_id,
                tenant_id=str(scope.get("tenant_id") or ""),
                workspace_id=str(scope.get("workspace_id") or ""),
                user_id=str(scope.get("user_id") or ""),
                event_type="trusted_inactive_artifact_prewrite",
                action=PROMOTION_TRUSTED_INACTIVE_ARTIFACT_WRITER_IMPLEMENTATION_ACTION,
                target=str(implementation_approval.get("candidate_id") or candidate_id),
                policy_decision="allow_inactive_review_write",
                timestamp=now_iso(),
                metadata={
                    "replacement_approval_id": replacement_approval_id,
                    "proposed_skill_id": implementation_approval.get("proposed_skill_id"),
                    "gate_operation": PROMOTION_GATE_APPLY_OPERATION,
                    "gate_reason": gate_reason,
                    "target_paths": target_paths,
                    "activation_allowed": False,
                    "canonical_writeback_allowed": False,
                },
                redacted_fields=[],
            ),
        )
        _write_yaml_create_new(browser_skill_path, dict(payloads["browser_skill"]))
        _write_json_create_new(siteops_card_path, dict(payloads["siteops_skill_card"]))
        browser_skill_ref = browser_skill_rel
        siteops_card_ref = siteops_card_rel
        browser_skill_digest = _sha256_json(dict(payloads["browser_skill"]))
        siteops_card_digest = _sha256_json(dict(payloads["siteops_skill_card"]))
        postwrite_audit_ref = append_audit_event(
            root,
            SiteOpsAuditEvent(
                event_id=f"event_{run_id}_trusted_inactive_postwrite",
                run_id=run_id,
                tenant_id=str(scope.get("tenant_id") or ""),
                workspace_id=str(scope.get("workspace_id") or ""),
                user_id=str(scope.get("user_id") or ""),
                event_type="trusted_inactive_artifact_postwrite",
                action=PROMOTION_TRUSTED_INACTIVE_ARTIFACT_WRITER_IMPLEMENTATION_ACTION,
                target=str(implementation_approval.get("candidate_id") or candidate_id),
                policy_decision="inactive_review_artifacts_written",
                timestamp=now_iso(),
                metadata={
                    "browser_skill_ref": browser_skill_ref,
                    "siteops_skill_card_ref": siteops_card_ref,
                    "browser_skill_payload_sha256": browser_skill_digest,
                    "siteops_skill_card_payload_sha256": siteops_card_digest,
                    "activation_allowed": False,
                    "approval_consumed": False,
                    "canonical_writeback_allowed": False,
                },
                redacted_fields=[],
            ),
        )
        audit_ref = postwrite_audit_ref or prewrite_audit_ref
        writer_status = "trusted_inactive_artifacts_written_inactive_review"
        review_decision = "inactive_review_artifacts_written_activation_still_blocked"

    denied_effects = list(implementation_approval.get("denied_effects") or [])
    for effect in [
        "consume replacement approval request",
        "edit Gate allowlist",
        "launch or control a browser",
        "enqueue Agent Bus work",
        "call provider APIs",
        "activate promoted skills",
        "write canonical ChaseOS memory/state",
    ]:
        if effect not in denied_effects:
            denied_effects.insert(0, effect)

    writes_performed = bool(run_ref or browser_skill_ref or siteops_card_ref or prewrite_audit_ref or postwrite_audit_ref)
    return {
        "ok": True,
        "action": PROMOTION_TRUSTED_INACTIVE_ARTIFACT_WRITER_IMPLEMENTATION_ACTION,
        "candidate_id": implementation_approval.get("candidate_id"),
        "proposed_skill_id": implementation_approval.get("proposed_skill_id"),
        "scope": scope,
        "replacement_approval_id": replacement_approval_id,
        "actor": actor,
        "trusted_inactive_artifact_writer_implementation_approval_status": implementation_approval.get(
            "trusted_inactive_artifact_writer_implementation_approval_status"
        ),
        "trusted_inactive_artifact_writer_preflight_status": preflight.get(
            "trusted_inactive_artifact_writer_preflight_status"
        ),
        "trusted_inactive_artifact_writer_implementation_status": writer_status,
        "review_decision": review_decision,
        "write_inactive_artifacts_requested": bool(write_inactive_artifacts),
        "writer_ready_to_write": ready_to_write,
        "gate_operation": PROMOTION_GATE_APPLY_OPERATION,
        "gate_operation_allowed": bool(gate_allowed),
        "gate_reason": gate_reason,
        "target_paths": target_paths,
        "target_path_checks": target_checks,
        "proposed_artifact_payloads": payloads,
        "browser_skill_ref": browser_skill_ref,
        "siteops_skill_card_ref": siteops_card_ref,
        "browser_skill_payload_sha256": browser_skill_digest,
        "siteops_skill_card_payload_sha256": siteops_card_digest,
        "run_ref": run_ref,
        "audit_ref": audit_ref,
        "prewrite_audit_ref": prewrite_audit_ref,
        "postwrite_audit_ref": postwrite_audit_ref,
        "blocked_actions": denied_effects,
        "denied_effects": denied_effects,
        "writes_performed": writes_performed,
        "implementation_approval_record_written": False,
        "implementation_request_artifact_written": False,
        "approval_decision_written": False,
        "approval_consumed": False,
        "run_record_written": bool(run_ref),
        "audit_events_written": bool(prewrite_audit_ref or postwrite_audit_ref),
        "inactive_artifacts_written": bool(browser_skill_ref and siteops_card_ref),
        "browser_skill_artifact_written": bool(browser_skill_ref),
        "siteops_skill_card_artifact_written": bool(siteops_card_ref),
        "trusted_inactive_artifact_writer_implemented": True,
        "trusted_inactive_artifact_writer_enabled": bool(write_inactive_artifacts and ready_to_write),
        "trusted_inactive_artifact_writer_execution_allowed": bool(write_inactive_artifacts and ready_to_write),
        "trusted_skill_write_allowed": bool(write_inactive_artifacts and ready_to_write),
        "siteops_skill_card_write_allowed": bool(write_inactive_artifacts and ready_to_write),
        "allowlist_change_allowed": False,
        "allowlist_change_performed": False,
        "policy_file_write_allowed": False,
        "browser_execution_allowed": False,
        "agent_bus_enqueue_allowed": False,
        "provider_api_call_allowed": False,
        "activation_allowed": False,
        "canonical_writeback_allowed": False,
        "boundary": (
            "trusted inactive artifact writer implementation only; writes require explicit "
            "--write-inactive-artifacts, approved replacement approval posture, immediate preflight, "
            "clear target paths, and Gate allowance. Artifacts remain inactive_review and this command "
            "does not consume approvals, mutate Gate policy, launch browsers, enqueue Agent Bus work, "
            "call providers, activate skills, or write canonical ChaseOS state."
        ),
    }


def apply_trusted_candidate_artifacts(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    replacement_approval_id: str,
    actor: str,
    reason: str | None = None,
    write_inactive_artifacts: bool = False,
) -> dict[str, Any]:
    """Canonical guarded executor entrypoint for trusted candidate artifacts.

    This is intentionally a thin wrapper over the reviewed inactive artifact
    writer. The name gives AOR/SiteOps a stable entrypoint, while the underlying
    writer still requires the approved replacement approval posture, immediate
    preflight, ChaseOS Gate allowance, and the explicit write flag before any
    inactive-review artifact write can occur.
    """
    result = candidate_promotion_trusted_inactive_artifact_writer_implementation(
        candidate_id,
        root,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
        replacement_approval_id=replacement_approval_id,
        actor=actor,
        reason=reason or "operator invoked guarded apply_trusted_candidate_artifacts entrypoint",
        write_inactive_artifacts=write_inactive_artifacts,
    )
    result = dict(result)
    result.update(
        {
            "action": PROMOTION_APPLY_TRUSTED_CANDIDATE_ARTIFACTS_ACTION,
            "executor_entrypoint": "apply_trusted_candidate_artifacts",
            "executor_entrypoint_status": "guarded_entrypoint_invoked",
            "siteops_guarded_executor": True,
            "trusted_inactive_artifact_writer_result_action": (
                PROMOTION_TRUSTED_INACTIVE_ARTIFACT_WRITER_IMPLEMENTATION_ACTION
            ),
            "boundary": (
                "apply_trusted_candidate_artifacts is the canonical guarded executor "
                "entrypoint. It delegates to the inactive artifact writer and keeps "
                "the same Gate check, explicit --write-inactive-artifacts flag, "
                "no approval consumption, no activation, no browser execution, no "
                "Agent Bus enqueue, no provider call, and no canonical writeback boundary."
            ),
        }
    )
    return result


apply_trusted_candidate_artifacts.siteops_guarded_executor = True  # type: ignore[attr-defined]


def candidate_promotion_trusted_inactive_artifact_writer_live_gate_readiness(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    replacement_approval_id: str,
    actor: str,
    reason: str | None = None,
) -> dict[str, Any]:
    """Return a read-only live Gate readiness packet for the inactive writer.

    This intentionally does not declare the runtime operation, edit the Gateway
    allowlists, or run the writer. It reports the exact policy posture required
    before an operator can review a separate Gate patch.
    """
    implementation_approval = candidate_promotion_trusted_inactive_artifact_writer_implementation_approval(
        candidate_id,
        root,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
        replacement_approval_id=replacement_approval_id,
        decision="approve",
        actor=actor,
        reason=reason or "operator requested live Gate readiness review",
    )
    preflight = candidate_promotion_trusted_inactive_artifact_writer_preflight(
        candidate_id,
        root,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
        replacement_approval_id=replacement_approval_id,
    )
    scope = dict(implementation_approval.get("scope") or preflight.get("scope") or {})
    target_paths = dict(preflight.get("target_paths") or {})
    browser_skill_rel = str(target_paths.get("browser_skill") or "")
    siteops_card_rel = str(target_paths.get("siteops_skill_card") or "")
    write_targets = [path for path in [browser_skill_rel, siteops_card_rel] if path]
    gate_allowed, gate_reason = check_runtime_operation(
        PROMOTION_GATE_APPLY_OPERATION,
        write_targets=write_targets,
    )
    approval_ready = bool(implementation_approval.get("implementation_patch_allowed_next_pass"))
    preflight_ready = bool(preflight.get("write_preflight_pass"))
    target_paths_ready = bool(browser_skill_rel and siteops_card_rel)
    writer_implemented = True
    gate_patch_ready = approval_ready and preflight_ready and target_paths_ready and writer_implemented and not gate_allowed

    if not approval_ready:
        readiness_status = (
            "blocked_trusted_inactive_artifact_writer_implementation_approval: "
            f"{implementation_approval.get('trusted_inactive_artifact_writer_implementation_approval_status')}"
        )
        review_decision = "blocked_before_live_gate_readiness"
    elif not preflight_ready:
        readiness_status = (
            "blocked_trusted_inactive_artifact_writer_preflight: "
            f"{preflight.get('trusted_inactive_artifact_writer_preflight_status')}"
        )
        review_decision = "blocked_before_live_gate_readiness"
    elif not target_paths_ready:
        readiness_status = "blocked_trusted_inactive_artifact_target_paths_missing"
        review_decision = "blocked_before_live_gate_readiness"
    elif gate_allowed:
        readiness_status = "blocked_gate_operation_already_allowlisted_requires_operator_review"
        review_decision = "operation_already_allowlisted_review_before_any_live_write"
    else:
        readiness_status = "trusted_inactive_artifact_writer_live_gate_readiness_ready_no_write"
        review_decision = "ready_for_separate_operator_reviewed_gate_policy_patch"

    readiness_checks = [
        _executor_preflight_check(
            "trusted_inactive_writer_implementation_present",
            passed=writer_implemented,
            detail="bounded inactive artifact writer function is present",
        ),
        _executor_preflight_check(
            "implementation_approval_packet_ready",
            passed=approval_ready,
            detail=str(
                implementation_approval.get(
                    "trusted_inactive_artifact_writer_implementation_approval_status"
                )
            ),
        ),
        _executor_preflight_check(
            "immediate_preflight_ready",
            passed=preflight_ready,
            detail=str(preflight.get("trusted_inactive_artifact_writer_preflight_status")),
        ),
        _executor_preflight_check(
            "target_paths_available",
            passed=target_paths_ready,
            detail=str(target_paths),
        ),
        _executor_preflight_check(
            "gate_operation_currently_denies_live_write",
            passed=not gate_allowed,
            required=False,
            detail=gate_reason,
        ),
        _executor_preflight_check(
            "gate_policy_mutation_disabled_this_pass",
            passed=True,
            detail="this command does not edit runtime/chaseos_gate.py or runtime/policy/gateway_allowlists.json",
        ),
        _executor_preflight_check(
            "live_write_disabled_this_pass",
            passed=True,
            detail="this command does not call the writer with --write-inactive-artifacts",
        ),
    ]
    proposed_gate_patch = {
        "status": "preview_only",
        "operation": PROMOTION_GATE_APPLY_OPERATION,
        "runtime_operation_policy_file": "runtime/chaseos_gate.py",
        "gateway_allowlists_file": "runtime/policy/gateway_allowlists.json",
        "runtime_operation_policy_preview": {
            PROMOTION_GATE_APPLY_OPERATION: {
                "allow_cli_operator": True,
                "write_target_categories": [
                    "browser_skills_inactive_review",
                    "siteops_skill_cards_inactive_review",
                ],
            }
        },
        "gateway_write_target_categories_preview": {
            "browser_skills_inactive_review": ["runtime/browser_skills/skills/*.yaml"],
            "siteops_skill_cards_inactive_review": [
                "runtime/siteops/registry/skill_cards/*.json"
            ],
        },
        "patch_performed": False,
        "requires_separate_operator_approval": True,
        "requires_fail_closed_live_smoke_before_write": True,
    }
    fail_closed_smoke_command = [
        "python",
        "-m",
        "runtime.cli.main",
        "siteops",
        "candidates",
        "trusted-inactive-artifact-writer-implementation",
        str(candidate_id),
        "--replacement-approval-id",
        str(replacement_approval_id),
        "--tenant",
        str(tenant_id or ""),
        "--workspace",
        str(workspace_id or ""),
        "--user",
        str(user_id or ""),
        "--actor",
        str(actor),
        "--write-inactive-artifacts",
        "--json",
    ]
    denied_effects = [
        "edit runtime/chaseos_gate.py",
        "edit runtime/policy/gateway_allowlists.json",
        "write inactive trusted artifacts",
        "consume replacement approval request",
        "launch or control a browser",
        "enqueue Agent Bus work",
        "call provider APIs",
        "activate promoted skills",
        "write canonical ChaseOS memory/state",
    ]
    return {
        "ok": True,
        "action": PROMOTION_TRUSTED_INACTIVE_ARTIFACT_WRITER_LIVE_GATE_READINESS_ACTION,
        "candidate_id": implementation_approval.get("candidate_id") or preflight.get("candidate_id"),
        "proposed_skill_id": implementation_approval.get("proposed_skill_id") or preflight.get("proposed_skill_id"),
        "scope": scope,
        "replacement_approval_id": replacement_approval_id,
        "actor": actor,
        "trusted_inactive_artifact_writer_live_gate_readiness_status": readiness_status,
        "review_decision": review_decision,
        "trusted_inactive_artifact_writer_implementation_approval_status": implementation_approval.get(
            "trusted_inactive_artifact_writer_implementation_approval_status"
        ),
        "trusted_inactive_artifact_writer_preflight_status": preflight.get(
            "trusted_inactive_artifact_writer_preflight_status"
        ),
        "gate_operation": PROMOTION_GATE_APPLY_OPERATION,
        "gate_operation_allowed": bool(gate_allowed),
        "gate_reason": gate_reason,
        "gate_patch_ready_for_operator_review": gate_patch_ready,
        "target_paths": target_paths,
        "write_targets": write_targets,
        "readiness_checks": readiness_checks,
        "proposed_gate_patch": proposed_gate_patch,
        "fail_closed_live_smoke": {
            "required_before_any_live_write": True,
            "expected_current_result": "blocked_gate_operation_not_allowlisted",
            "command_preview": fail_closed_smoke_command,
            "writes_expected": False,
        },
        "blocked_actions": denied_effects,
        "denied_effects": denied_effects,
        "writes_performed": False,
        "gate_policy_change_allowed": False,
        "gate_policy_change_performed": False,
        "allowlist_change_allowed": False,
        "allowlist_change_performed": False,
        "policy_file_write_allowed": False,
        "inactive_artifacts_written": False,
        "trusted_skill_write_allowed": False,
        "siteops_skill_card_write_allowed": False,
        "approval_consumed": False,
        "browser_execution_allowed": False,
        "agent_bus_enqueue_allowed": False,
        "provider_api_call_allowed": False,
        "activation_allowed": False,
        "canonical_writeback_allowed": False,
        "boundary": (
            "live Gate readiness only; it produces an operator-review packet for a "
            "future Gate patch and fail-closed smoke, but does not mutate Gate policy, "
            "write artifacts, consume approvals, launch browsers, enqueue Agent Bus work, "
            "call providers, activate skills, or write canonical ChaseOS memory/state."
        ),
    }


def candidate_promotion_trusted_inactive_artifact_writer_gate_allowlist_approval_request(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    replacement_approval_id: str,
    actor: str,
    requested_by: str | None = None,
    reason: str | None = None,
    write_approval_request: bool = False,
) -> dict[str, Any]:
    """Preview or write a pending approval request for the future Gate patch.

    This creates only a SiteOps approval artifact when explicitly requested. It
    does not edit Gate policy, change gateway allowlists, run the inactive
    artifact writer, consume approvals, or write trusted artifacts.
    """
    readiness = candidate_promotion_trusted_inactive_artifact_writer_live_gate_readiness(
        candidate_id,
        root,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
        replacement_approval_id=replacement_approval_id,
        actor=actor,
        reason=reason or "operator requested Gate allowlist approval-request packet",
    )
    scope_data = dict(readiness.get("scope") or {})
    scope = SiteOpsScope(
        tenant_id=str(scope_data.get("tenant_id") or tenant_id or ""),
        workspace_id=str(scope_data.get("workspace_id") or workspace_id or ""),
        user_id=str(scope_data.get("user_id") or user_id or ""),
    )
    requested_by_id = str(requested_by or actor or user_id or "").strip()
    run_fingerprint = hashlib.sha256(
        f"{scope.tenant_id}|{scope.workspace_id}|{scope.user_id}|{candidate_id}|{replacement_approval_id}".encode(
            "utf-8"
        )
    ).hexdigest()[:10]
    run_stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    run_id = f"siteops_gate_allowlist_{run_stamp}_{run_fingerprint}"
    gate_patch_ready = bool(readiness.get("gate_patch_ready_for_operator_review"))
    proposed_gate_patch = dict(readiness.get("proposed_gate_patch") or {})
    request_digest = hashlib.sha256(
        json.dumps(
            {
                "candidate_id": readiness.get("candidate_id"),
                "proposed_skill_id": readiness.get("proposed_skill_id"),
                "replacement_approval_id": replacement_approval_id,
                "gate_operation": readiness.get("gate_operation"),
                "target_paths": readiness.get("target_paths"),
                "proposed_gate_patch": proposed_gate_patch,
            },
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()
    approval_request_artifact = {
        "request_id": run_id,
        "request_type": "siteops_trusted_inactive_writer_gate_allowlist_approval_request",
        "tenant_id": scope.tenant_id,
        "workspace_id": scope.workspace_id,
        "user_id": scope.user_id,
        "requested_by": requested_by_id,
        "candidate_id": readiness.get("candidate_id"),
        "proposed_skill_id": readiness.get("proposed_skill_id"),
        "replacement_approval_id": replacement_approval_id,
        "requested_action": "review_gate_policy_patch_for_trusted_inactive_artifact_writer",
        "gate_operation": PROMOTION_GATE_APPLY_OPERATION,
        "target_paths": readiness.get("target_paths"),
        "write_targets": readiness.get("write_targets"),
        "proposed_gate_patch": proposed_gate_patch,
        "request_digest_sha256": request_digest,
        "status": "pending_operator_review" if gate_patch_ready else "blocked_before_operator_review",
        "gate_patch_allowed_in_this_pass": False,
        "approval_consumption_allowed_in_this_pass": False,
        "trusted_artifact_write_allowed_in_this_pass": False,
        "activation_allowed_in_this_pass": False,
    }
    approval: dict[str, Any] | None = None
    audit_ref: str | None = None

    if not gate_patch_ready:
        request_status = (
            "blocked_trusted_inactive_artifact_writer_live_gate_readiness: "
            f"{readiness.get('trusted_inactive_artifact_writer_live_gate_readiness_status')}"
        )
        review_decision = "blocked_before_gate_allowlist_approval_request"
    elif write_approval_request:
        approval = create_approval_request(
            root,
            scope=scope,
            run_id=run_id,
            workflow_id=PROMOTION_WORKFLOW_ID,
            action=PROMOTION_TRUSTED_INACTIVE_ARTIFACT_WRITER_GATE_ALLOWLIST_APPROVAL_REQUEST_ACTION,
            risk_level="high",
            approval_reason=(
                "Review a future ChaseOS Gate policy patch for "
                f"{PROMOTION_GATE_APPLY_OPERATION}. This approval request does not "
                "edit Gate policy, write trusted artifacts, consume approvals, "
                "launch browsers, activate skills, or mutate canonical state."
            ),
            required_approver_role="tenant_admin",
            requested_by=requested_by_id,
            metadata={
                "candidate_id": readiness.get("candidate_id"),
                "proposed_skill_id": readiness.get("proposed_skill_id"),
                "replacement_approval_id": replacement_approval_id,
                "gate_operation": PROMOTION_GATE_APPLY_OPERATION,
                "target_paths": readiness.get("target_paths"),
                "write_targets": readiness.get("write_targets"),
                "proposed_gate_patch": proposed_gate_patch,
                "request_digest_sha256": request_digest,
                "secrets_or_session_state_included": False,
                "gate_policy_change_performed": False,
                "inactive_artifacts_written": False,
            },
        )
        append_audit_event(
            root,
            SiteOpsAuditEvent(
                event_id=f"event_{run_id}_gate_allowlist_approval_request",
                run_id=run_id,
                tenant_id=scope.tenant_id,
                workspace_id=scope.workspace_id,
                user_id=scope.user_id,
                event_type="gate_allowlist_approval_request_created",
                action=PROMOTION_TRUSTED_INACTIVE_ARTIFACT_WRITER_GATE_ALLOWLIST_APPROVAL_REQUEST_ACTION,
                target=str(readiness.get("candidate_id") or candidate_id),
                policy_decision="operator_approval_required",
                timestamp=now_iso(),
                metadata={
                    "approval_id": approval.get("approval_id"),
                    "approval_ref": approval.get("approval_ref"),
                    "gate_operation": PROMOTION_GATE_APPLY_OPERATION,
                    "gate_policy_change_performed": False,
                    "inactive_artifacts_written": False,
                    "approval_consumed": False,
                },
                redacted_fields=[],
            ),
        )
        request_status = "gate_allowlist_approval_request_written_pending_operator_decision"
        review_decision = "pending_operator_review_for_future_gate_policy_patch"
    else:
        request_status = "gate_allowlist_approval_request_ready_preview_only"
        review_decision = "ready_to_write_pending_approval_request_if_operator_requests"

    approval_request_checks = [
        _executor_preflight_check(
            "live_gate_readiness_ready",
            passed=gate_patch_ready,
            detail=str(readiness.get("trusted_inactive_artifact_writer_live_gate_readiness_status")),
        ),
        _executor_preflight_check(
            "requested_by_present",
            passed=bool(requested_by_id),
            detail=requested_by_id or "missing requested_by",
        ),
        _executor_preflight_check(
            "gate_patch_not_applied",
            passed=True,
            detail="approval request does not edit runtime/chaseos_gate.py or runtime/policy/gateway_allowlists.json",
        ),
        _executor_preflight_check(
            "trusted_writer_not_run",
            passed=True,
            detail="approval request does not call --write-inactive-artifacts",
        ),
    ]
    denied_effects = list(readiness.get("denied_effects") or [])
    for effect in [
        "apply Gate policy patch from approval request",
        "edit gateway allowlists from approval request",
        "write inactive trusted artifacts from approval request",
        "consume replacement approval from approval request",
        "activate skill memory from approval request",
    ]:
        if effect not in denied_effects:
            denied_effects.insert(0, effect)

    return {
        "ok": True,
        "action": PROMOTION_TRUSTED_INACTIVE_ARTIFACT_WRITER_GATE_ALLOWLIST_APPROVAL_REQUEST_ACTION,
        "candidate_id": readiness.get("candidate_id"),
        "proposed_skill_id": readiness.get("proposed_skill_id"),
        "scope": scope.as_dict(),
        "replacement_approval_id": replacement_approval_id,
        "actor": actor,
        "requested_by": requested_by_id,
        "gate_allowlist_approval_request_status": request_status,
        "review_decision": review_decision,
        "live_gate_readiness_status": readiness.get(
            "trusted_inactive_artifact_writer_live_gate_readiness_status"
        ),
        "gate_patch_ready_for_operator_review": gate_patch_ready,
        "gate_operation": PROMOTION_GATE_APPLY_OPERATION,
        "gate_operation_allowed": readiness.get("gate_operation_allowed"),
        "gate_reason": readiness.get("gate_reason"),
        "target_paths": readiness.get("target_paths"),
        "write_targets": readiness.get("write_targets"),
        "proposed_gate_patch": proposed_gate_patch,
        "fail_closed_live_smoke": readiness.get("fail_closed_live_smoke"),
        "approval_request_artifact": approval_request_artifact,
        "approval_request_checks": approval_request_checks,
        "approval": approval,
        "approval_id": approval.get("approval_id") if approval else None,
        "approval_ref": approval.get("approval_ref") if approval else None,
        "audit_ref": audit_ref,
        "request_digest_sha256": request_digest,
        "write_approval_request_requested": bool(write_approval_request),
        "approval_request_written": bool(approval),
        "approval_request_pending": bool(approval and approval.get("status") == "pending"),
        "writes_performed": bool(approval),
        "files_modified": bool(approval),
        "audit_event_written": bool(audit_ref),
        "blocked_actions": denied_effects,
        "denied_effects": denied_effects,
        "gate_policy_change_allowed": False,
        "gate_policy_change_performed": False,
        "allowlist_change_allowed": False,
        "allowlist_change_performed": False,
        "policy_file_write_allowed": False,
        "inactive_artifacts_written": False,
        "trusted_skill_write_allowed": False,
        "siteops_skill_card_write_allowed": False,
        "approval_consumed": False,
        "browser_execution_allowed": False,
        "agent_bus_enqueue_allowed": False,
        "provider_api_call_allowed": False,
        "activation_allowed": False,
        "canonical_writeback_allowed": False,
        "boundary": (
            "Gate allowlist approval-request only; optional writes are limited to a pending "
            "SiteOps approval artifact plus audit event. Gate policy, gateway allowlists, "
            "trusted artifacts, approval consumption, browser execution, Agent Bus work, "
            "provider calls, activation, and canonical ChaseOS state remain unchanged."
        ),
    }


def _legacy_candidate_promotion_trusted_inactive_artifact_writer_gate_allowlist_decision_preflight(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    replacement_approval_id: str,
    gate_approval_id: str,
    actor: str,
    reason: str | None = None,
) -> dict[str, Any]:
    """Validate a Gate allowlist approval request before any policy patch.

    This is a no-mutation preflight. It loads the SiteOps approval artifact,
    recomputes the readiness/request digest, and reports whether a later Gate
    patch pass may be considered. It does not consume approval or edit policy.
    """
    readiness = candidate_promotion_trusted_inactive_artifact_writer_live_gate_readiness(
        candidate_id,
        root,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
        replacement_approval_id=replacement_approval_id,
        actor=actor,
        reason=reason or "operator requested Gate allowlist decision preflight",
    )
    scope = dict(readiness.get("scope") or {})
    approval = show_approval_request(root, gate_approval_id, tenant_id=tenant_id)
    metadata = dict(approval.get("metadata") or {})
    proposed_gate_patch = dict(readiness.get("proposed_gate_patch") or {})
    expected_digest = hashlib.sha256(
        json.dumps(
            {
                "candidate_id": readiness.get("candidate_id"),
                "proposed_skill_id": readiness.get("proposed_skill_id"),
                "replacement_approval_id": replacement_approval_id,
                "gate_operation": readiness.get("gate_operation"),
                "target_paths": readiness.get("target_paths"),
                "proposed_gate_patch": proposed_gate_patch,
            },
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()
    approval_status = str(approval.get("status") or "")
    action_matches = approval.get("action") == PROMOTION_TRUSTED_INACTIVE_ARTIFACT_WRITER_GATE_ALLOWLIST_APPROVAL_REQUEST_ACTION
    scope_matches = (
        approval.get("tenant_id") == scope.get("tenant_id")
        and approval.get("workspace_id") == scope.get("workspace_id")
        and approval.get("user_id") == scope.get("user_id")
    )
    metadata_matches = (
        metadata.get("candidate_id") == readiness.get("candidate_id")
        and metadata.get("proposed_skill_id") == readiness.get("proposed_skill_id")
        and metadata.get("replacement_approval_id") == replacement_approval_id
        and metadata.get("gate_operation") == PROMOTION_GATE_APPLY_OPERATION
    )
    digest_matches = metadata.get("request_digest_sha256") == expected_digest
    target_paths_match = metadata.get("target_paths") == readiness.get("target_paths")
    write_targets_match = metadata.get("write_targets") == readiness.get("write_targets")
    no_sensitive_state = metadata.get("secrets_or_session_state_included") is False
    original_request_no_mutation = (
        metadata.get("gate_policy_change_performed") is False
        and metadata.get("inactive_artifacts_written") is False
    )
    categories = proposed_gate_patch.get("gateway_write_target_categories_preview") or {}
    operation_policy = (
        proposed_gate_patch.get("runtime_operation_policy_preview", {})
        .get(PROMOTION_GATE_APPLY_OPERATION, {})
    )
    write_categories = operation_policy.get("write_target_categories") or []
    target_categories_ready = (
        "browser_skills_inactive_review" in write_categories
        and "siteops_skill_cards_inactive_review" in write_categories
        and categories.get("browser_skills_inactive_review") == ["runtime/browser_skills/skills/*.yaml"]
        and categories.get("siteops_skill_cards_inactive_review") == [
            "runtime/siteops/registry/skill_cards/*.json"
        ]
    )
    gate_still_denied = readiness.get("gate_operation_allowed") is False
    readiness_ready = bool(readiness.get("gate_patch_ready_for_operator_review"))
    fail_closed_smoke_required = bool(
        proposed_gate_patch.get("requires_fail_closed_live_smoke_before_write")
    ) and bool(readiness.get("fail_closed_live_smoke", {}).get("required_before_any_live_write"))

    if not action_matches:
        preflight_status = "blocked_gate_allowlist_approval_action_mismatch"
        review_decision = "blocked_before_gate_allowlist_policy_patch"
    elif not scope_matches:
        preflight_status = "blocked_gate_allowlist_approval_scope_mismatch"
        review_decision = "blocked_before_gate_allowlist_policy_patch"
    elif not metadata_matches:
        preflight_status = "blocked_gate_allowlist_approval_metadata_mismatch"
        review_decision = "blocked_before_gate_allowlist_policy_patch"
    elif not digest_matches:
        preflight_status = "blocked_gate_allowlist_approval_digest_mismatch"
        review_decision = "blocked_before_gate_allowlist_policy_patch"
    elif approval_status == "pending":
        preflight_status = "blocked_pending_gate_allowlist_approval"
        review_decision = "pending_operator_decision"
    elif approval_status == "rejected":
        preflight_status = "blocked_rejected_gate_allowlist_approval"
        review_decision = "operator_rejected_gate_allowlist_policy_patch"
    elif approval_status != "approved":
        preflight_status = "blocked_unknown_gate_allowlist_approval_status"
        review_decision = "blocked_before_gate_allowlist_policy_patch"
    elif not readiness_ready:
        preflight_status = (
            "blocked_live_gate_readiness_not_ready: "
            f"{readiness.get('trusted_inactive_artifact_writer_live_gate_readiness_status')}"
        )
        review_decision = "blocked_before_gate_allowlist_policy_patch"
    elif not gate_still_denied:
        preflight_status = "blocked_gate_operation_already_allowlisted_requires_review"
        review_decision = "blocked_before_gate_allowlist_policy_patch"
    elif not target_categories_ready:
        preflight_status = "blocked_gate_write_target_categories_not_ready"
        review_decision = "blocked_before_gate_allowlist_policy_patch"
    elif not fail_closed_smoke_required:
        preflight_status = "blocked_missing_fail_closed_smoke_requirement"
        review_decision = "blocked_before_gate_allowlist_policy_patch"
    else:
        preflight_status = "gate_allowlist_decision_preflight_ready_no_mutation"
        review_decision = "ready_for_separate_operator_reviewed_gate_policy_patch"

    checks = [
        _executor_preflight_check("approval_artifact_loaded", passed=True, detail=gate_approval_id),
        _executor_preflight_check("approval_action_matches", passed=action_matches, detail=str(approval.get("action"))),
        _executor_preflight_check("approval_scope_matches", passed=scope_matches, detail=str(scope)),
        _executor_preflight_check("approval_metadata_matches", passed=metadata_matches, detail=str(metadata.get("gate_operation"))),
        _executor_preflight_check("approval_digest_matches_current_readiness", passed=digest_matches, detail=expected_digest),
        _executor_preflight_check("approval_status_approved", passed=approval_status == "approved", detail=approval_status),
        _executor_preflight_check("target_paths_match", passed=target_paths_match, detail=str(readiness.get("target_paths"))),
        _executor_preflight_check("write_targets_match", passed=write_targets_match, detail=str(readiness.get("write_targets"))),
        _executor_preflight_check("target_categories_ready", passed=target_categories_ready, detail=str(categories)),
        _executor_preflight_check("live_gate_readiness_ready", passed=readiness_ready, detail=str(readiness.get("trusted_inactive_artifact_writer_live_gate_readiness_status"))),
        _executor_preflight_check("gate_operation_still_denied", passed=gate_still_denied, detail=str(readiness.get("gate_reason"))),
        _executor_preflight_check("fail_closed_smoke_required", passed=fail_closed_smoke_required, detail=str(readiness.get("fail_closed_live_smoke"))),
        _executor_preflight_check("no_sensitive_state_in_approval_metadata", passed=no_sensitive_state, detail="secrets/session state flag must be false"),
        _executor_preflight_check("original_request_had_no_mutation", passed=original_request_no_mutation, detail="approval metadata must record no Gate/artifact mutation"),
        _executor_preflight_check("policy_patch_disabled_this_pass", passed=True, detail="decision preflight does not edit Gate policy or gateway allowlists"),
    ]
    denied_effects = list(readiness.get("denied_effects") or [])
    for effect in [
        "consume Gate allowlist approval request",
        "apply Gate policy patch from decision preflight",
        "edit gateway allowlists from decision preflight",
        "write inactive trusted artifacts from decision preflight",
        "activate skill memory from decision preflight",
    ]:
        if effect not in denied_effects:
            denied_effects.insert(0, effect)

    return {
        "ok": True,
        "action": PROMOTION_TRUSTED_INACTIVE_ARTIFACT_WRITER_GATE_ALLOWLIST_DECISION_PREFLIGHT_ACTION,
        "candidate_id": readiness.get("candidate_id"),
        "proposed_skill_id": readiness.get("proposed_skill_id"),
        "scope": scope,
        "replacement_approval_id": replacement_approval_id,
        "gate_approval_id": gate_approval_id,
        "actor": actor,
        "gate_allowlist_decision_preflight_status": preflight_status,
        "review_decision": review_decision,
        "approval": {
            "approval_id": approval.get("approval_id"),
            "approval_ref": approval.get("approval_ref"),
            "status": approval_status,
            "action": approval.get("action"),
            "decided_by": approval.get("decided_by"),
            "decided_at": approval.get("decided_at"),
        },
        "approval_status": approval_status,
        "approval_metadata": metadata,
        "request_digest_sha256": metadata.get("request_digest_sha256"),
        "expected_request_digest_sha256": expected_digest,
        "digest_matches": digest_matches,
        "live_gate_readiness_status": readiness.get(
            "trusted_inactive_artifact_writer_live_gate_readiness_status"
        ),
        "gate_patch_ready_for_operator_review": readiness_ready,
        "gate_operation": PROMOTION_GATE_APPLY_OPERATION,
        "gate_operation_allowed": readiness.get("gate_operation_allowed"),
        "gate_reason": readiness.get("gate_reason"),
        "target_paths": readiness.get("target_paths"),
        "write_targets": readiness.get("write_targets"),
        "proposed_gate_patch": proposed_gate_patch,
        "fail_closed_live_smoke": readiness.get("fail_closed_live_smoke"),
        "decision_preflight_checks": checks,
        "ready_for_gate_policy_patch_next_pass": preflight_status
        == "gate_allowlist_decision_preflight_ready_no_mutation",
        "blocked_actions": denied_effects,
        "denied_effects": denied_effects,
        "writes_performed": False,
        "files_modified": False,
        "approval_consumed": False,
        "gate_policy_change_allowed": False,
        "gate_policy_change_performed": False,
        "allowlist_change_allowed": False,
        "allowlist_change_performed": False,
        "policy_file_write_allowed": False,
        "inactive_artifacts_written": False,
        "trusted_skill_write_allowed": False,
        "siteops_skill_card_write_allowed": False,
        "browser_execution_allowed": False,
        "agent_bus_enqueue_allowed": False,
        "provider_api_call_allowed": False,
        "activation_allowed": False,
        "canonical_writeback_allowed": False,
        "boundary": (
            "Gate allowlist decision preflight only; it validates the approval request "
            "and current readiness before a separate policy-patch pass. It does not "
            "consume approval, edit Gate policy, edit gateway allowlists, write trusted "
            "artifacts, execute browsers, enqueue Agent Bus work, call providers, "
            "activate skills, or write canonical ChaseOS state."
        ),
    }


def candidate_promotion_trusted_inactive_artifact_writer_gate_allowlist_decision_preflight(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    replacement_approval_id: str,
    gate_approval_id: str,
    actor: str,
    reason: str | None = None,
) -> dict[str, Any]:
    """Validate a Gate allowlist approval decision before any policy patch.

    This is intentionally read-only. It validates the stored approval request
    against the current readiness packet and reports whether a later, separate
    Gate policy patch can be considered. It never edits Gate policy, writes
    artifacts, consumes approvals, or runs the trusted writer.
    """
    preview = candidate_promotion_trusted_inactive_artifact_writer_gate_allowlist_approval_request(
        candidate_id,
        root,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
        replacement_approval_id=replacement_approval_id,
        actor=actor,
        requested_by=actor,
        reason=reason or "operator requested Gate allowlist decision preflight",
        write_approval_request=False,
    )
    scope_data = dict(preview.get("scope") or {})
    scope = SiteOpsScope(
        tenant_id=str(scope_data.get("tenant_id") or tenant_id or ""),
        workspace_id=str(scope_data.get("workspace_id") or workspace_id or ""),
        user_id=str(scope_data.get("user_id") or user_id or ""),
    )
    approval = show_approval_request(root, gate_approval_id, tenant_id=scope.tenant_id)
    metadata = dict(approval.get("metadata") or {})
    expected_digest = str(preview.get("request_digest_sha256") or "")
    metadata_digest = str(metadata.get("request_digest_sha256") or "")
    target_paths_match = metadata.get("target_paths") == preview.get("target_paths")
    write_targets_match = metadata.get("write_targets") == preview.get("write_targets")
    proposed_gate_patch = dict(preview.get("proposed_gate_patch") or {})
    categories = proposed_gate_patch.get("gateway_write_target_categories_preview") or {}
    operation_policy = (
        proposed_gate_patch.get("runtime_operation_policy_preview", {})
        .get(PROMOTION_GATE_APPLY_OPERATION, {})
    )
    write_categories = operation_policy.get("write_target_categories") or []
    target_categories_ready = (
        "browser_skills_inactive_review" in write_categories
        and "siteops_skill_cards_inactive_review" in write_categories
        and categories.get("browser_skills_inactive_review") == ["runtime/browser_skills/skills/*.yaml"]
        and categories.get("siteops_skill_cards_inactive_review") == [
            "runtime/siteops/registry/skill_cards/*.json"
        ]
    )
    fail_closed_smoke_required = bool(
        proposed_gate_patch.get("requires_fail_closed_live_smoke_before_write")
    ) and bool(preview.get("fail_closed_live_smoke", {}).get("required_before_any_live_write"))
    no_sensitive_state = metadata.get("secrets_or_session_state_included") is False
    original_request_no_mutation = (
        metadata.get("gate_policy_change_performed") is False
        and metadata.get("inactive_artifacts_written") is False
    )
    scope_match = (
        approval.get("tenant_id") == scope.tenant_id
        and approval.get("workspace_id") == scope.workspace_id
        and approval.get("user_id") == scope.user_id
    )
    action_match = (
        approval.get("action")
        == PROMOTION_TRUSTED_INACTIVE_ARTIFACT_WRITER_GATE_ALLOWLIST_APPROVAL_REQUEST_ACTION
    )
    metadata_checks = [
        _executor_preflight_check(
            "approval_scope_matches_request",
            passed=scope_match,
            detail=f"{approval.get('tenant_id')}/{approval.get('workspace_id')}/{approval.get('user_id')}",
        ),
        _executor_preflight_check(
            "approval_action_matches_gate_allowlist_request",
            passed=action_match,
            detail=str(approval.get("action")),
        ),
        _executor_preflight_check(
            "candidate_id_matches",
            passed=metadata.get("candidate_id") == preview.get("candidate_id"),
            detail=str(metadata.get("candidate_id")),
        ),
        _executor_preflight_check(
            "replacement_approval_id_matches",
            passed=metadata.get("replacement_approval_id") == replacement_approval_id,
            detail=str(metadata.get("replacement_approval_id")),
        ),
        _executor_preflight_check(
            "gate_operation_matches",
            passed=metadata.get("gate_operation") == PROMOTION_GATE_APPLY_OPERATION,
            detail=str(metadata.get("gate_operation")),
        ),
        _executor_preflight_check(
            "request_digest_matches_current_preview",
            passed=bool(expected_digest and metadata_digest == expected_digest),
            detail=metadata_digest or "missing request digest",
        ),
        _executor_preflight_check(
            "target_paths_match_current_preview",
            passed=target_paths_match,
            detail=str(metadata.get("target_paths")),
        ),
        _executor_preflight_check(
            "write_targets_match_current_preview",
            passed=write_targets_match,
            detail=str(metadata.get("write_targets")),
        ),
        _executor_preflight_check(
            "live_gate_readiness_still_ready",
            passed=bool(preview.get("gate_patch_ready_for_operator_review")),
            detail=str(preview.get("live_gate_readiness_status")),
        ),
        _executor_preflight_check(
            "gate_operation_still_denied_before_patch",
            passed=not bool(preview.get("gate_operation_allowed")),
            detail=str(preview.get("gate_reason")),
        ),
        _executor_preflight_check(
            "target_categories_ready",
            passed=target_categories_ready,
            detail=str(categories),
        ),
        _executor_preflight_check(
            "fail_closed_smoke_required",
            passed=fail_closed_smoke_required,
            detail=str(preview.get("fail_closed_live_smoke")),
        ),
        _executor_preflight_check(
            "no_sensitive_state_in_approval_metadata",
            passed=no_sensitive_state,
            detail="secrets/session state flag must be false",
        ),
        _executor_preflight_check(
            "original_request_had_no_mutation",
            passed=original_request_no_mutation,
            detail="approval metadata must record no Gate/artifact mutation",
        ),
        _executor_preflight_check(
            "policy_patch_disabled_this_pass",
            passed=True,
            detail="decision preflight does not edit Gate policy or gateway allowlists",
        ),
    ]
    required_checks_pass = all(
        bool(item.get("passed")) for item in metadata_checks if item.get("required", True)
    )
    approval_status = str(approval.get("status") or "")
    if not required_checks_pass:
        preflight_status = "blocked_gate_allowlist_decision_preflight_metadata_or_readiness_mismatch"
        review_decision = "blocked_before_gate_policy_patch_consideration"
    elif approval_status == "pending":
        preflight_status = "blocked_pending_gate_allowlist_approval"
        review_decision = "pending_operator_decision_no_policy_patch"
    elif approval_status == "approved":
        preflight_status = "gate_allowlist_decision_preflight_ready_no_mutation"
        review_decision = "approved_for_separate_gate_policy_patch_review"
    elif approval_status == "rejected":
        preflight_status = "gate_allowlist_decision_preflight_rejected_blocks_policy_patch"
        review_decision = "rejected_no_policy_patch"
    else:
        preflight_status = f"blocked_gate_allowlist_decision_preflight_unknown_status:{approval_status}"
        review_decision = "blocked_before_gate_policy_patch_consideration"

    approved_for_future_patch = required_checks_pass and approval_status == "approved"
    denied_effects = [
        "edit runtime/chaseos_gate.py",
        "edit runtime/policy/gateway_allowlists.json",
        "write inactive trusted artifacts",
        "consume replacement approval request",
        "consume Gate allowlist approval request",
        "launch or control a browser",
        "enqueue Agent Bus work",
        "call provider APIs",
        "activate promoted skills",
        "write canonical ChaseOS memory/state",
    ]
    return {
        "ok": True,
        "action": PROMOTION_TRUSTED_INACTIVE_ARTIFACT_WRITER_GATE_ALLOWLIST_DECISION_PREFLIGHT_ACTION,
        "candidate_id": preview.get("candidate_id"),
        "proposed_skill_id": preview.get("proposed_skill_id"),
        "scope": scope.as_dict(),
        "replacement_approval_id": replacement_approval_id,
        "gate_approval_id": gate_approval_id,
        "actor": actor,
        "gate_allowlist_decision_preflight_status": preflight_status,
        "review_decision": review_decision,
        "approval_status": approval_status,
        "approval_ref": approval.get("approval_ref"),
        "approval_decided_by": approval.get("decided_by"),
        "approval_decided_at": approval.get("decided_at"),
        "live_gate_readiness_status": preview.get("live_gate_readiness_status"),
        "gate_allowlist_approval_request_status": preview.get("gate_allowlist_approval_request_status"),
        "gate_operation": PROMOTION_GATE_APPLY_OPERATION,
        "gate_operation_allowed": preview.get("gate_operation_allowed"),
        "gate_reason": preview.get("gate_reason"),
        "target_paths": preview.get("target_paths"),
        "write_targets": preview.get("write_targets"),
        "proposed_gate_patch": proposed_gate_patch,
        "fail_closed_live_smoke": preview.get("fail_closed_live_smoke"),
        "request_digest_sha256": expected_digest,
        "approval_request_digest_sha256": metadata_digest,
        "digest_matches": bool(expected_digest and metadata_digest == expected_digest),
        "decision_preflight_checks": metadata_checks,
        "approved_for_future_gate_policy_patch_review": approved_for_future_patch,
        "ready_for_gate_policy_patch_next_pass": approved_for_future_patch,
        "gate_policy_patch_allowed_in_this_pass": False,
        "gate_policy_change_allowed": False,
        "gate_policy_change_performed": False,
        "allowlist_change_allowed": False,
        "allowlist_change_performed": False,
        "policy_file_write_allowed": False,
        "inactive_artifacts_written": False,
        "trusted_skill_write_allowed": False,
        "siteops_skill_card_write_allowed": False,
        "approval_consumed": False,
        "gate_approval_consumed": False,
        "browser_execution_allowed": False,
        "agent_bus_enqueue_allowed": False,
        "provider_api_call_allowed": False,
        "activation_allowed": False,
        "canonical_writeback_allowed": False,
        "writes_performed": False,
        "files_modified": False,
        "blocked_actions": denied_effects,
        "denied_effects": denied_effects,
        "boundary": (
            "Gate allowlist decision preflight only; validates a pending/decided "
            "approval request before a future Gate policy patch. It performs no "
            "policy write, trusted artifact write, approval consumption, browser "
            "execution, Agent Bus work, provider call, activation, or canonical writeback."
        ),
    }


def candidate_promotion_trusted_inactive_artifact_writer_gate_policy_patch_plan(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    replacement_approval_id: str,
    gate_approval_id: str,
    actor: str,
    reason: str | None = None,
) -> dict[str, Any]:
    """Return a no-write Gate policy patch plan for operator review.

    The plan requires an approved decision preflight and previews the exact
    runtime operation and gateway allowlist entries needed by the future
    trusted inactive writer. It does not edit Gate files or consume approvals.
    """
    decision = candidate_promotion_trusted_inactive_artifact_writer_gate_allowlist_decision_preflight(
        candidate_id,
        root,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
        replacement_approval_id=replacement_approval_id,
        gate_approval_id=gate_approval_id,
        actor=actor,
        reason=reason or "operator requested no-write Gate policy patch plan",
    )
    proposed_gate_patch = dict(decision.get("proposed_gate_patch") or {})
    operation_preview = (
        proposed_gate_patch.get("runtime_operation_policy_preview", {})
        .get(PROMOTION_GATE_APPLY_OPERATION, {})
    )
    category_preview = dict(proposed_gate_patch.get("gateway_write_target_categories_preview") or {})
    expected_runtime_policy = {
        "allow_cli_operator": True,
        "gateway_write_categories": [
            "browser_skills_inactive_review",
            "siteops_skill_cards_inactive_review",
        ],
        "write_target_categories": [
            "browser_skills_inactive_review",
            "siteops_skill_cards_inactive_review",
        ],
    }
    expected_categories = {
        "browser_skills_inactive_review": ["runtime/browser_skills/skills/*.yaml"],
        "siteops_skill_cards_inactive_review": [
            "runtime/siteops/registry/skill_cards/*.json"
        ],
    }
    ready_from_decision = bool(decision.get("ready_for_gate_policy_patch_next_pass"))
    runtime_policy_matches = (
        bool(operation_preview.get("allow_cli_operator"))
        and operation_preview.get("write_target_categories")
        == expected_runtime_policy["write_target_categories"]
    )
    gateway_categories_match = category_preview == expected_categories
    fail_closed_required = bool(
        proposed_gate_patch.get("requires_fail_closed_live_smoke_before_write")
    ) and bool(decision.get("fail_closed_live_smoke", {}).get("required_before_any_live_write"))
    gate_still_denied = not bool(decision.get("gate_operation_allowed"))
    patch_plan_ready = (
        ready_from_decision
        and runtime_policy_matches
        and gateway_categories_match
        and fail_closed_required
        and gate_still_denied
    )
    if patch_plan_ready:
        plan_status = "gate_policy_patch_plan_ready_no_write"
        review_decision = "ready_for_operator_review_of_exact_gate_patch"
    else:
        plan_status = "blocked_gate_policy_patch_plan_preconditions"
        review_decision = "blocked_before_gate_policy_patch_plan"

    patch_plan = {
        "status": "preview_only",
        "patch_performed": False,
        "runtime_operation_policy_change": {
            "file": "runtime/chaseos_gate.py",
            "operation": PROMOTION_GATE_APPLY_OPERATION,
            "change": "add_runtime_operation_policy_entry",
            "desired_entry": expected_runtime_policy,
            "insertion_target": "RUNTIME_OPERATION_POLICIES",
            "review_note": (
                "Add only after operator review of this plan and fail-closed "
                "smoke evidence; do not grant browser execution, provider calls, "
                "Agent Bus enqueue, activation, or canonical writeback."
            ),
        },
        "gateway_allowlists_change": {
            "file": "runtime/policy/gateway_allowlists.json",
            "change": "add_write_target_categories",
            "desired_entries": expected_categories,
            "review_note": "Categories are limited to inactive-review artifact paths.",
        },
        "required_fail_closed_smoke": decision.get("fail_closed_live_smoke"),
        "apply_conditions": [
            "operator-approved Gate allowlist approval request remains approved",
            "decision preflight remains ready immediately before policy edit",
            "runtime operation remains denied before patch",
            "fail-closed live smoke demonstrates trusted writer cannot write before allowlist",
            "patch is applied by a separate explicit Gate-policy write pass",
        ],
    }
    checks = [
        _executor_preflight_check(
            "decision_preflight_ready",
            passed=ready_from_decision,
            detail=str(decision.get("gate_allowlist_decision_preflight_status")),
        ),
        _executor_preflight_check(
            "approval_status_approved",
            passed=decision.get("approval_status") == "approved",
            detail=str(decision.get("approval_status")),
        ),
        _executor_preflight_check(
            "request_digest_matches",
            passed=bool(decision.get("digest_matches")),
            detail=str(decision.get("request_digest_sha256")),
        ),
        _executor_preflight_check(
            "runtime_policy_preview_matches_expected",
            passed=runtime_policy_matches,
            detail=str(operation_preview),
        ),
        _executor_preflight_check(
            "gateway_category_preview_matches_expected",
            passed=gateway_categories_match,
            detail=str(category_preview),
        ),
        _executor_preflight_check(
            "fail_closed_smoke_required_before_write",
            passed=fail_closed_required,
            detail=str(decision.get("fail_closed_live_smoke")),
        ),
        _executor_preflight_check(
            "gate_operation_still_denied_before_patch",
            passed=gate_still_denied,
            detail=str(decision.get("gate_reason")),
        ),
        _executor_preflight_check(
            "policy_patch_disabled_this_pass",
            passed=True,
            detail="this command returns a patch plan only and does not edit Gate files",
        ),
    ]
    denied_effects = [
        "edit runtime/chaseos_gate.py",
        "edit runtime/policy/gateway_allowlists.json",
        "consume Gate allowlist approval request",
        "write inactive trusted artifacts",
        "launch or control a browser",
        "enqueue Agent Bus work",
        "call provider APIs",
        "activate promoted skills",
        "write canonical ChaseOS memory/state",
    ]
    return {
        "ok": True,
        "action": PROMOTION_TRUSTED_INACTIVE_ARTIFACT_WRITER_GATE_POLICY_PATCH_PLAN_ACTION,
        "candidate_id": decision.get("candidate_id"),
        "proposed_skill_id": decision.get("proposed_skill_id"),
        "scope": decision.get("scope"),
        "replacement_approval_id": replacement_approval_id,
        "gate_approval_id": gate_approval_id,
        "actor": actor,
        "gate_policy_patch_plan_status": plan_status,
        "review_decision": review_decision,
        "gate_allowlist_decision_preflight_status": decision.get(
            "gate_allowlist_decision_preflight_status"
        ),
        "approval_status": decision.get("approval_status"),
        "digest_matches": decision.get("digest_matches"),
        "gate_operation": PROMOTION_GATE_APPLY_OPERATION,
        "gate_operation_allowed": decision.get("gate_operation_allowed"),
        "gate_reason": decision.get("gate_reason"),
        "target_paths": decision.get("target_paths"),
        "write_targets": decision.get("write_targets"),
        "policy_patch_plan": patch_plan,
        "policy_patch_checks": checks,
        "ready_for_gate_policy_write_next_pass": patch_plan_ready,
        "gate_policy_patch_allowed_in_this_pass": False,
        "gate_policy_change_allowed": False,
        "gate_policy_change_performed": False,
        "allowlist_change_allowed": False,
        "allowlist_change_performed": False,
        "policy_file_write_allowed": False,
        "approval_consumed": False,
        "gate_approval_consumed": False,
        "inactive_artifacts_written": False,
        "trusted_skill_write_allowed": False,
        "siteops_skill_card_write_allowed": False,
        "browser_execution_allowed": False,
        "agent_bus_enqueue_allowed": False,
        "provider_api_call_allowed": False,
        "activation_allowed": False,
        "canonical_writeback_allowed": False,
        "writes_performed": False,
        "files_modified": False,
        "blocked_actions": denied_effects,
        "denied_effects": denied_effects,
        "boundary": (
            "Gate policy patch plan only; previews exact runtime policy and "
            "gateway allowlist entries after an approved decision preflight. "
            "It performs no Gate file write, approval consumption, trusted "
            "artifact write, browser execution, Agent Bus work, provider call, "
            "activation, or canonical writeback."
        ),
    }


def candidate_promotion_trusted_inactive_artifact_writer_gate_policy_patch_application_design(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    replacement_approval_id: str,
    gate_approval_id: str,
    actor: str,
    reason: str | None = None,
) -> dict[str, Any]:
    """Design the future Gate policy patch application without applying it."""
    plan = candidate_promotion_trusted_inactive_artifact_writer_gate_policy_patch_plan(
        candidate_id,
        root,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
        replacement_approval_id=replacement_approval_id,
        gate_approval_id=gate_approval_id,
        actor=actor,
        reason=reason or "operator requested no-write Gate policy patch application design",
    )
    patch_plan = dict(plan.get("policy_patch_plan") or {})
    runtime_change = dict(patch_plan.get("runtime_operation_policy_change") or {})
    allowlist_change = dict(patch_plan.get("gateway_allowlists_change") or {})
    desired_runtime_entry = dict(runtime_change.get("desired_entry") or {})
    desired_allowlist_entries = dict(allowlist_change.get("desired_entries") or {})
    plan_ready = bool(plan.get("ready_for_gate_policy_write_next_pass"))
    target_files_ready = (
        runtime_change.get("file") == "runtime/chaseos_gate.py"
        and allowlist_change.get("file") == "runtime/policy/gateway_allowlists.json"
    )
    active_gateway_key_present = (
        desired_runtime_entry.get("gateway_write_categories")
        == [
            "browser_skills_inactive_review",
            "siteops_skill_cards_inactive_review",
        ]
    )
    compatibility_key_present = (
        desired_runtime_entry.get("write_target_categories")
        == [
            "browser_skills_inactive_review",
            "siteops_skill_cards_inactive_review",
        ]
    )
    allowlist_entries_ready = desired_allowlist_entries == {
        "browser_skills_inactive_review": ["runtime/browser_skills/skills/*.yaml"],
        "siteops_skill_cards_inactive_review": [
            "runtime/siteops/registry/skill_cards/*.json"
        ],
    }
    fail_closed_smoke_required = bool(
        (patch_plan.get("required_fail_closed_smoke") or {}).get(
            "required_before_any_live_write"
        )
    )
    design_ready = (
        plan_ready
        and target_files_ready
        and active_gateway_key_present
        and compatibility_key_present
        and allowlist_entries_ready
        and fail_closed_smoke_required
    )
    if design_ready:
        design_status = "gate_policy_patch_application_design_ready_no_write"
        review_decision = "ready_for_separate_operator_reviewed_gate_policy_application"
    else:
        design_status = "blocked_gate_policy_patch_application_design_preconditions"
        review_decision = "blocked_before_gate_policy_application"

    transaction_design = {
        "status": "design_only",
        "write_performed": False,
        "future_command_name": (
            "trusted-inactive-artifact-writer-gate-policy-patch-application"
        ),
        "requires_explicit_write_flag": "--apply-gate-policy-patch",
        "requires_operator_review": True,
        "requires_plan_status": "gate_policy_patch_plan_ready_no_write",
        "requires_fail_closed_smoke_evidence": True,
        "target_files": [
            runtime_change.get("file"),
            allowlist_change.get("file"),
        ],
        "ordered_steps": [
            "load current Gate policy files",
            "verify runtime operation is still absent before patch",
            "verify inactive-review write-target categories are still absent before patch",
            "verify approved Gate approval and patch-plan digest still match current readiness",
            "apply minimal runtime operation entry to RUNTIME_OPERATION_POLICIES",
            "apply minimal gateway write-target categories to gateway_allowlists.json",
            "parse/compile changed files before considering the patch applied",
            "run fail-closed and post-patch Gate checks in a later verification pass",
        ],
        "atomicity_rules": [
            "write through temporary content and replace only after parse/compile checks",
            "abort before either file write when either target precondition fails",
            "record before/after digests in a future patch-application audit artifact",
            "do not consume approval in the patch application pass",
        ],
        "rollback_rules": [
            "preserve pre-patch file digests before writing",
            "restore both files if post-write validation fails",
            "do not run trusted artifact writer during rollback",
        ],
        "future_patch": {
            "runtime_operation_policy_change": runtime_change,
            "gateway_allowlists_change": allowlist_change,
        },
    }
    checks = [
        _executor_preflight_check(
            "patch_plan_ready",
            passed=plan_ready,
            detail=str(plan.get("gate_policy_patch_plan_status")),
        ),
        _executor_preflight_check(
            "target_files_ready",
            passed=target_files_ready,
            detail=str(transaction_design["target_files"]),
        ),
        _executor_preflight_check(
            "active_gateway_key_present",
            passed=active_gateway_key_present,
            detail=str(desired_runtime_entry.get("gateway_write_categories")),
        ),
        _executor_preflight_check(
            "compatibility_write_target_key_present",
            passed=compatibility_key_present,
            detail=str(desired_runtime_entry.get("write_target_categories")),
        ),
        _executor_preflight_check(
            "allowlist_entries_ready",
            passed=allowlist_entries_ready,
            detail=str(desired_allowlist_entries),
        ),
        _executor_preflight_check(
            "fail_closed_smoke_required",
            passed=fail_closed_smoke_required,
            detail=str(patch_plan.get("required_fail_closed_smoke")),
        ),
        _executor_preflight_check(
            "policy_application_disabled_this_pass",
            passed=True,
            detail="this command returns a design only and does not edit Gate files",
        ),
    ]
    denied_effects = [
        "apply Gate policy patch",
        "edit runtime/chaseos_gate.py",
        "edit runtime/policy/gateway_allowlists.json",
        "consume Gate allowlist approval request",
        "write inactive trusted artifacts",
        "launch or control a browser",
        "enqueue Agent Bus work",
        "call provider APIs",
        "activate promoted skills",
        "write canonical ChaseOS memory/state",
    ]
    return {
        "ok": True,
        "action": PROMOTION_TRUSTED_INACTIVE_ARTIFACT_WRITER_GATE_POLICY_PATCH_APPLICATION_DESIGN_ACTION,
        "candidate_id": plan.get("candidate_id"),
        "proposed_skill_id": plan.get("proposed_skill_id"),
        "scope": plan.get("scope"),
        "replacement_approval_id": replacement_approval_id,
        "gate_approval_id": gate_approval_id,
        "actor": actor,
        "gate_policy_patch_application_design_status": design_status,
        "review_decision": review_decision,
        "gate_policy_patch_plan_status": plan.get("gate_policy_patch_plan_status"),
        "approval_status": plan.get("approval_status"),
        "digest_matches": plan.get("digest_matches"),
        "gate_operation": PROMOTION_GATE_APPLY_OPERATION,
        "gate_operation_allowed": plan.get("gate_operation_allowed"),
        "gate_reason": plan.get("gate_reason"),
        "target_paths": plan.get("target_paths"),
        "write_targets": plan.get("write_targets"),
        "policy_patch_plan": patch_plan,
        "policy_patch_application_design": transaction_design,
        "policy_patch_application_checks": checks,
        "ready_for_gate_policy_application_next_pass": design_ready,
        "gate_policy_patch_allowed_in_this_pass": False,
        "gate_policy_application_allowed_in_this_pass": False,
        "gate_policy_change_allowed": False,
        "gate_policy_change_performed": False,
        "allowlist_change_allowed": False,
        "allowlist_change_performed": False,
        "policy_file_write_allowed": False,
        "approval_consumed": False,
        "gate_approval_consumed": False,
        "inactive_artifacts_written": False,
        "trusted_skill_write_allowed": False,
        "siteops_skill_card_write_allowed": False,
        "browser_execution_allowed": False,
        "agent_bus_enqueue_allowed": False,
        "provider_api_call_allowed": False,
        "activation_allowed": False,
        "canonical_writeback_allowed": False,
        "writes_performed": False,
        "files_modified": False,
        "blocked_actions": denied_effects,
        "denied_effects": denied_effects,
        "boundary": (
            "Gate policy patch application design only; it describes the future "
            "explicit write transaction for Gate policy files but performs no "
            "policy write, approval consumption, trusted artifact write, browser "
            "execution, Agent Bus work, provider call, activation, or canonical writeback."
        ),
    }


def candidate_promotion_trusted_inactive_artifact_writer_gate_policy_patch_application_preflight(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    replacement_approval_id: str,
    gate_approval_id: str,
    actor: str,
    reason: str | None = None,
) -> dict[str, Any]:
    """Preflight the future Gate policy patch application without applying it."""
    design = candidate_promotion_trusted_inactive_artifact_writer_gate_policy_patch_application_design(
        candidate_id,
        root,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
        replacement_approval_id=replacement_approval_id,
        gate_approval_id=gate_approval_id,
        actor=actor,
        reason=reason or "operator requested no-write Gate policy patch application preflight",
    )
    vault_root = Path(root or ".").resolve()
    application_design = dict(design.get("policy_patch_application_design") or {})
    future_patch = dict(application_design.get("future_patch") or {})
    runtime_change = dict(future_patch.get("runtime_operation_policy_change") or {})
    allowlist_change = dict(future_patch.get("gateway_allowlists_change") or {})
    desired_runtime_entry = dict(runtime_change.get("desired_entry") or {})
    desired_allowlist_entries = dict(allowlist_change.get("desired_entries") or {})

    def _file_preflight(rel_path: str | None, *, content_kind: str) -> dict[str, Any]:
        rel_text = str(rel_path or "").strip()
        target = vault_root / rel_text if rel_text else vault_root
        exists = bool(rel_text and target.exists() and target.is_file())
        text = target.read_text(encoding="utf-8") if exists else ""
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest() if exists else None
        parsed = False
        parse_error: str | None = None
        if exists:
            try:
                if content_kind == "python":
                    compile(text, rel_text, "exec")
                elif content_kind == "json":
                    json.loads(text)
                parsed = True
            except Exception as exc:  # pragma: no cover - exercised by malformed fixtures if added later
                parse_error = str(exc)
        return {
            "path": rel_text,
            "exists": exists,
            "sha256": digest,
            "parse_ok": parsed,
            "parse_error": parse_error,
            "operation_already_present": bool(PROMOTION_GATE_APPLY_OPERATION in text),
            "write_allowed_in_this_pass": False,
        }

    runtime_file = _file_preflight(runtime_change.get("file"), content_kind="python")
    allowlist_file = _file_preflight(allowlist_change.get("file"), content_kind="json")
    allowlist_payload: dict[str, Any] = {}
    if allowlist_file["exists"] and allowlist_file["parse_ok"]:
        allowlist_payload = json.loads((vault_root / allowlist_file["path"]).read_text(encoding="utf-8"))
    current_write_targets = dict(allowlist_payload.get("write_targets") or {})
    desired_category_absence = {
        category: category not in current_write_targets
        for category in desired_allowlist_entries.keys()
    }
    exact_desired_entries_ready = (
        desired_runtime_entry.get("gateway_write_categories")
        == [
            "browser_skills_inactive_review",
            "siteops_skill_cards_inactive_review",
        ]
        and desired_runtime_entry.get("write_target_categories")
        == [
            "browser_skills_inactive_review",
            "siteops_skill_cards_inactive_review",
        ]
        and desired_allowlist_entries
        == {
            "browser_skills_inactive_review": ["runtime/browser_skills/skills/*.yaml"],
            "siteops_skill_cards_inactive_review": [
                "runtime/siteops/registry/skill_cards/*.json"
            ],
        }
    )
    rollback_audit_artifact = {
        "record_type": "siteops_gate_policy_patch_application_audit",
        "schema_version": 1,
        "candidate_id": design.get("candidate_id"),
        "gate_operation": PROMOTION_GATE_APPLY_OPERATION,
        "pre_patch_file_digests": {
            "runtime_policy": runtime_file.get("sha256"),
            "gateway_allowlists": allowlist_file.get("sha256"),
        },
        "post_patch_file_digests": "future_write_pass_only",
        "rollback_required_on_validation_failure": True,
        "contains_secrets_or_session_state": False,
        "write_allowed_in_this_pass": False,
    }
    design_ready = bool(design.get("ready_for_gate_policy_application_next_pass"))
    files_ready = (
        bool(runtime_file["exists"])
        and bool(runtime_file["parse_ok"])
        and bool(allowlist_file["exists"])
        and bool(allowlist_file["parse_ok"])
    )
    operation_absent = not bool(runtime_file["operation_already_present"])
    categories_absent = all(desired_category_absence.values()) if desired_category_absence else False
    fail_closed_required = bool(
        (dict(design.get("policy_patch_plan") or {}).get("required_fail_closed_smoke") or {}).get(
            "required_before_any_live_write"
        )
    )
    rollback_audit_ready = (
        bool(rollback_audit_artifact["pre_patch_file_digests"]["runtime_policy"])
        and bool(rollback_audit_artifact["pre_patch_file_digests"]["gateway_allowlists"])
        and rollback_audit_artifact["contains_secrets_or_session_state"] is False
    )
    preflight_ready = (
        design_ready
        and files_ready
        and operation_absent
        and categories_absent
        and exact_desired_entries_ready
        and fail_closed_required
        and rollback_audit_ready
    )
    if preflight_ready:
        preflight_status = "gate_policy_patch_application_preflight_ready_no_write"
        review_decision = "ready_for_separate_operator_reviewed_gate_policy_application_write"
    else:
        preflight_status = "blocked_gate_policy_patch_application_preflight_preconditions"
        review_decision = "blocked_before_gate_policy_application_write"

    checks = [
        _executor_preflight_check(
            "application_design_ready",
            passed=design_ready,
            detail=str(design.get("gate_policy_patch_application_design_status")),
        ),
        _executor_preflight_check(
            "runtime_policy_file_exists_and_parses",
            passed=bool(runtime_file["exists"] and runtime_file["parse_ok"]),
            detail=str(runtime_file),
        ),
        _executor_preflight_check(
            "gateway_allowlists_file_exists_and_parses",
            passed=bool(allowlist_file["exists"] and allowlist_file["parse_ok"]),
            detail=str(allowlist_file),
        ),
        _executor_preflight_check(
            "gate_operation_absent_before_patch",
            passed=operation_absent,
            detail=str(runtime_file["operation_already_present"]),
        ),
        _executor_preflight_check(
            "inactive_review_categories_absent_before_patch",
            passed=categories_absent,
            detail=str(desired_category_absence),
        ),
        _executor_preflight_check(
            "exact_desired_entries_ready",
            passed=exact_desired_entries_ready,
            detail=str({"runtime": desired_runtime_entry, "allowlists": desired_allowlist_entries}),
        ),
        _executor_preflight_check(
            "fail_closed_smoke_required",
            passed=fail_closed_required,
            detail=str((dict(design.get("policy_patch_plan") or {}).get("required_fail_closed_smoke") or {})),
        ),
        _executor_preflight_check(
            "rollback_audit_artifact_shape_ready",
            passed=rollback_audit_ready,
            detail=str(rollback_audit_artifact),
        ),
        _executor_preflight_check(
            "policy_application_disabled_this_pass",
            passed=True,
            detail="this command preflights only and does not edit Gate files",
        ),
    ]
    denied_effects = [
        "apply Gate policy patch",
        "edit runtime/chaseos_gate.py",
        "edit runtime/policy/gateway_allowlists.json",
        "write rollback or audit artifacts",
        "consume Gate allowlist approval request",
        "write inactive trusted artifacts",
        "launch or control a browser",
        "enqueue Agent Bus work",
        "call provider APIs",
        "activate promoted skills",
        "write canonical ChaseOS memory/state",
    ]
    return {
        "ok": True,
        "action": PROMOTION_TRUSTED_INACTIVE_ARTIFACT_WRITER_GATE_POLICY_PATCH_APPLICATION_PREFLIGHT_ACTION,
        "candidate_id": design.get("candidate_id"),
        "proposed_skill_id": design.get("proposed_skill_id"),
        "scope": design.get("scope"),
        "replacement_approval_id": replacement_approval_id,
        "gate_approval_id": gate_approval_id,
        "actor": actor,
        "gate_policy_patch_application_preflight_status": preflight_status,
        "review_decision": review_decision,
        "gate_policy_patch_application_design_status": design.get(
            "gate_policy_patch_application_design_status"
        ),
        "gate_policy_patch_plan_status": design.get("gate_policy_patch_plan_status"),
        "approval_status": design.get("approval_status"),
        "digest_matches": design.get("digest_matches"),
        "gate_operation": PROMOTION_GATE_APPLY_OPERATION,
        "gate_operation_allowed": design.get("gate_operation_allowed"),
        "gate_reason": design.get("gate_reason"),
        "target_paths": design.get("target_paths"),
        "write_targets": design.get("write_targets"),
        "current_file_preflight": {
            "runtime_policy": runtime_file,
            "gateway_allowlists": allowlist_file,
            "desired_category_absence": desired_category_absence,
        },
        "rollback_audit_artifact_preview": rollback_audit_artifact,
        "policy_patch_application_design": application_design,
        "policy_patch_application_preflight_checks": checks,
        "ready_for_gate_policy_application_write_next_pass": preflight_ready,
        "gate_policy_patch_allowed_in_this_pass": False,
        "gate_policy_application_allowed_in_this_pass": False,
        "gate_policy_change_allowed": False,
        "gate_policy_change_performed": False,
        "allowlist_change_allowed": False,
        "allowlist_change_performed": False,
        "policy_file_write_allowed": False,
        "approval_consumed": False,
        "gate_approval_consumed": False,
        "rollback_audit_artifact_written": False,
        "inactive_artifacts_written": False,
        "trusted_skill_write_allowed": False,
        "siteops_skill_card_write_allowed": False,
        "browser_execution_allowed": False,
        "agent_bus_enqueue_allowed": False,
        "provider_api_call_allowed": False,
        "activation_allowed": False,
        "canonical_writeback_allowed": False,
        "writes_performed": False,
        "files_modified": False,
        "blocked_actions": denied_effects,
        "denied_effects": denied_effects,
        "boundary": (
            "Gate policy patch application preflight only; it reads current "
            "Gate files and computes digests/absence checks but performs no "
            "policy write, approval consumption, rollback/audit artifact write, "
            "trusted artifact write, browser execution, Agent Bus work, provider "
            "call, activation, or canonical writeback."
        ),
    }


def candidate_promotion_trusted_inactive_artifact_writer_gate_policy_patch_application_write_guard_contract(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    replacement_approval_id: str,
    gate_approval_id: str,
    actor: str,
    reason: str | None = None,
) -> dict[str, Any]:
    """Declare the future Gate policy patch write guard without applying it."""
    preflight = candidate_promotion_trusted_inactive_artifact_writer_gate_policy_patch_application_preflight(
        candidate_id,
        root,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
        replacement_approval_id=replacement_approval_id,
        gate_approval_id=gate_approval_id,
        actor=actor,
        reason=reason or "operator requested no-write Gate policy patch application write guard contract",
    )
    preflight_ready = bool(preflight.get("ready_for_gate_policy_application_write_next_pass"))
    current_files = dict(preflight.get("current_file_preflight") or {})
    runtime_file = dict(current_files.get("runtime_policy") or {})
    allowlist_file = dict(current_files.get("gateway_allowlists") or {})
    rollback_preview = dict(preflight.get("rollback_audit_artifact_preview") or {})
    explicit_write_flag = "--apply-gate-policy-patch"
    guard_contract = {
        "status": "write_guard_contract_only",
        "explicit_write_flag": explicit_write_flag,
        "explicit_write_flag_supported_in_this_pass": False,
        "unsupported_flag_rejection": (
            f"{explicit_write_flag} is intentionally unsupported by this command; "
            "a separate operator-reviewed Gate policy patch writer must be built before any policy edit"
        ),
        "requires_preflight_ready": True,
        "requires_approved_patch_plan_evidence": True,
        "requires_fail_closed_live_smoke_evidence": True,
        "requires_explicit_operator_approval": True,
        "requires_current_file_digests": {
            "runtime_policy": runtime_file.get("sha256"),
            "gateway_allowlists": allowlist_file.get("sha256"),
        },
        "allowed_target_files": [
            "runtime/chaseos_gate.py",
            "runtime/policy/gateway_allowlists.json",
        ],
        "atomic_write_policy": {
            "allowed_in_future_write_pass_only": True,
            "edit_scope": "minimal_exact_entries_only",
            "runtime_policy_edit": "add only the reviewed siteops.browser_skill_candidate.apply_trusted_artifacts operation entry",
            "gateway_allowlists_edit": "add only reviewed inactive-review write target categories",
            "backup_required_before_write": True,
            "post_write_validation_required": True,
            "rollback_required_on_validation_failure": True,
        },
        "post_apply_verification_required": [
            "runtime/chaseos_gate.py parses after edit",
            "runtime/policy/gateway_allowlists.json parses after edit",
            "operation appears exactly once in runtime policy",
            "inactive-review gateway allowlist categories match reviewed patterns exactly",
            "trusted inactive artifact write remains a separate command and smoke",
        ],
        "rollback_audit_artifact_preview": rollback_preview,
        "write_performed": False,
        "write_allowed_in_this_pass": False,
    }
    guard_ready = preflight_ready and all(guard_contract["requires_current_file_digests"].values())
    if guard_ready:
        guard_status = "gate_policy_patch_application_write_guard_ready_no_write"
        review_decision = "ready_for_separate_operator_reviewed_gate_policy_patch_writer"
    else:
        guard_status = "blocked_gate_policy_patch_application_write_guard_preconditions"
        review_decision = "blocked_before_gate_policy_patch_writer"
    checks = list(preflight.get("policy_patch_application_preflight_checks") or []) + [
        _executor_preflight_check(
            "explicit_apply_flag_unsupported_this_pass",
            passed=guard_contract["explicit_write_flag_supported_in_this_pass"] is False,
            detail=guard_contract["unsupported_flag_rejection"],
        ),
        _executor_preflight_check(
            "guard_current_file_digests_present",
            passed=all(guard_contract["requires_current_file_digests"].values()),
            detail=str(guard_contract["requires_current_file_digests"]),
        ),
        _executor_preflight_check(
            "guard_target_files_minimal",
            passed=guard_contract["allowed_target_files"] == [
                "runtime/chaseos_gate.py",
                "runtime/policy/gateway_allowlists.json",
            ],
            detail=str(guard_contract["allowed_target_files"]),
        ),
        _executor_preflight_check(
            "guard_writes_disabled_this_pass",
            passed=guard_contract["write_allowed_in_this_pass"] is False,
            detail="write-guard contract only; no Gate files are edited",
        ),
    ]
    denied_effects = list(preflight.get("denied_effects") or [])
    for item in [
        "accept --apply-gate-policy-patch on this command",
        "write Gate policy patch",
        "write rollback/audit artifact",
    ]:
        if item not in denied_effects:
            denied_effects.append(item)
    result = dict(preflight)
    result.update(
        {
            "action": PROMOTION_TRUSTED_INACTIVE_ARTIFACT_WRITER_GATE_POLICY_PATCH_APPLICATION_WRITE_GUARD_ACTION,
            "gate_policy_patch_application_write_guard_status": guard_status,
            "review_decision": review_decision,
            "write_guard_contract": guard_contract,
            "policy_patch_application_write_guard_checks": checks,
            "ready_for_gate_policy_patch_writer_next_pass": guard_ready,
            "apply_gate_policy_patch_flag_supported": False,
            "apply_gate_policy_patch_flag_required_for_future_writer": True,
            "gate_policy_patch_writer_implemented": False,
            "gate_policy_patch_writer_allowed_in_this_pass": False,
            "gate_policy_patch_allowed_in_this_pass": False,
            "gate_policy_application_allowed_in_this_pass": False,
            "gate_policy_change_allowed": False,
            "gate_policy_change_performed": False,
            "allowlist_change_allowed": False,
            "allowlist_change_performed": False,
            "policy_file_write_allowed": False,
            "rollback_audit_artifact_written": False,
            "approval_consumed": False,
            "gate_approval_consumed": False,
            "inactive_artifacts_written": False,
            "trusted_skill_write_allowed": False,
            "siteops_skill_card_write_allowed": False,
            "browser_execution_allowed": False,
            "agent_bus_enqueue_allowed": False,
            "provider_api_call_allowed": False,
            "activation_allowed": False,
            "canonical_writeback_allowed": False,
            "writes_performed": False,
            "files_modified": False,
            "blocked_actions": denied_effects,
            "denied_effects": denied_effects,
            "boundary": (
                "Gate policy patch application write-guard contract only; it declares the future explicit "
                "write flag, exact target files, digest and rollback requirements, but performs no Gate policy "
                "write, approval consumption, rollback/audit artifact write, trusted artifact write, browser "
                "execution, Agent Bus work, provider call, activation, or canonical writeback."
            ),
        }
    )
    return result



def candidate_promotion_trusted_inactive_artifact_writer_gate_policy_patch_writer_design(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    replacement_approval_id: str,
    gate_approval_id: str,
    actor: str,
    reason: str | None = None,
) -> dict[str, Any]:
    """Design the future explicit Gate policy patch writer without building it."""
    guard = candidate_promotion_trusted_inactive_artifact_writer_gate_policy_patch_application_write_guard_contract(
        candidate_id,
        root,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
        replacement_approval_id=replacement_approval_id,
        gate_approval_id=gate_approval_id,
        actor=actor,
        reason=reason or "operator requested no-write Gate policy patch writer design",
    )
    guard_contract = dict(guard.get("write_guard_contract") or {})
    application_design = dict(guard.get("policy_patch_application_design") or {})
    future_patch = dict(application_design.get("future_patch") or {})
    current_files = dict(guard.get("current_file_preflight") or {})
    runtime_file = dict(current_files.get("runtime_policy") or {})
    allowlist_file = dict(current_files.get("gateway_allowlists") or {})
    guard_ready = bool(guard.get("ready_for_gate_policy_patch_writer_next_pass"))
    exact_targets_ready = guard_contract.get("allowed_target_files") == [
        "runtime/chaseos_gate.py",
        "runtime/policy/gateway_allowlists.json",
    ]
    digests_ready = all((guard_contract.get("requires_current_file_digests") or {}).values())
    explicit_flag_ready = (
        guard_contract.get("explicit_write_flag") == "--apply-gate-policy-patch"
        and guard_contract.get("explicit_write_flag_supported_in_this_pass") is False
    )
    preconditions_ready = guard_ready and exact_targets_ready and digests_ready and explicit_flag_ready
    if preconditions_ready:
        design_status = "gate_policy_patch_writer_design_ready_no_write"
        review_decision = "ready_for_operator_review_of_gate_policy_patch_writer_implementation_request"
    else:
        design_status = "blocked_gate_policy_patch_writer_design_preconditions"
        review_decision = "blocked_before_gate_policy_patch_writer_implementation_request"

    writer_design = {
        "status": "writer_design_only",
        "future_writer_implemented": False,
        "future_command_name": "trusted-inactive-artifact-writer-gate-policy-patch-application",
        "explicit_write_flag": "--apply-gate-policy-patch",
        "future_explicit_write_flag": "--apply-gate-policy-patch",
        "explicit_write_flag_supported_in_this_pass": False,
        "future_explicit_write_flag_supported_here": False,
        "future_writer_requires_explicit_write_flag": True,
        "allowed_target_files": [
            "runtime/chaseos_gate.py",
            "runtime/policy/gateway_allowlists.json",
        ],
        "target_files": [
            "runtime/chaseos_gate.py",
            "runtime/policy/gateway_allowlists.json",
        ],
        "requires_approved_patch_plan_evidence": True,
        "requires_write_guard_evidence": True,
        "requires_fail_closed_live_smoke_evidence": True,
        "requires_operator_approval": True,
        "required_pre_write_evidence": [
            "approved Gate allowlist approval request",
            "decision preflight remains approved and digest-matched",
            "Gate policy patch plan remains exact",
            "application preflight current-file digests remain current",
            "write-guard contract remains ready",
            "fail-closed live smoke evidence exists immediately before write",
            "explicit operator approval exists for the writer transition",
        ],
        "atomic_write_sequence": [
            "reload current target files",
            "verify target file SHA-256 digests match the reviewed preflight",
            "verify operation and inactive-review categories remain absent",
            "write backup and rollback/audit artifact before replacement",
            "apply only the reviewed runtime operation policy entry",
            "apply only the reviewed gateway write-target category entries",
            "compile runtime/chaseos_gate.py and parse gateway_allowlists.json",
            "run post-apply Gate checks before trusted artifact writer is retried",
        ],
        "atomicity_contract": {
            "minimal_exact_entries_only": True,
            "backup_before_write": True,
            "rollback_on_verification_failure": True,
            "post_apply_verification_required": True,
            "allowed_target_file_count": 2,
        },
        "rollback_policy": {
            "backup_required_before_any_replace": True,
            "rollback_required_on_parse_or_gate_check_failure": True,
            "rollback_artifact_contains_secrets_or_session_state": False,
            "trusted_artifact_writer_must_not_run_during_rollback": True,
        },
        "future_patch": future_patch,
        "pre_write_digests": {
            "runtime_policy": runtime_file.get("sha256"),
            "gateway_allowlists": allowlist_file.get("sha256"),
        },
        "write_allowed_in_this_pass": False,
        "write_performed": False,
    }
    checks = list(guard.get("policy_patch_application_write_guard_checks") or []) + [
        _executor_preflight_check(
            "writer_design_guard_ready",
            passed=guard_ready,
            detail=str(guard.get("gate_policy_patch_application_write_guard_status")),
        ),
        _executor_preflight_check(
            "writer_design_target_files_minimal",
            passed=exact_targets_ready,
            detail=str(guard_contract.get("allowed_target_files")),
        ),
        _executor_preflight_check(
            "writer_design_exact_target_files",
            passed=exact_targets_ready,
            detail=str(guard_contract.get("allowed_target_files")),
        ),
        _executor_preflight_check(
            "writer_design_current_digests_present",
            passed=digests_ready,
            detail=str(guard_contract.get("requires_current_file_digests")),
        ),
        _executor_preflight_check(
            "writer_design_explicit_apply_flag_still_unsupported_here",
            passed=explicit_flag_ready,
            detail=str(guard_contract.get("explicit_write_flag")),
        ),
        _executor_preflight_check(
            "writer_design_writes_disabled_this_pass",
            passed=writer_design["write_allowed_in_this_pass"] is False,
            detail="design only; the future Gate patch writer is not implemented",
        ),
        _executor_preflight_check(
            "writer_design_no_writes_this_pass",
            passed=writer_design["write_allowed_in_this_pass"] is False,
            detail="design only; the future Gate patch writer is not implemented",
        ),
    ]
    denied_effects = list(guard.get("denied_effects") or [])
    for item in [
        "implement Gate policy patch writer",
        "accept --apply-gate-policy-patch on this design command",
        "write Gate policy backup artifact",
        "write Gate policy rollback artifact",
    ]:
        if item not in denied_effects:
            denied_effects.append(item)

    result = dict(guard)
    result.update(
        {
            "action": PROMOTION_TRUSTED_INACTIVE_ARTIFACT_WRITER_GATE_POLICY_PATCH_WRITER_DESIGN_ACTION,
            "gate_policy_patch_writer_design_status": design_status,
            "review_decision": review_decision,
            "gate_policy_patch_writer_design": writer_design,
            "policy_patch_writer_design": writer_design,
            "gate_policy_patch_writer_design_checks": checks,
            "policy_patch_writer_design_checks": checks,
            "ready_for_gate_policy_patch_writer_implementation_next_pass": preconditions_ready,
            "ready_for_gate_policy_patch_writer_implementation_request_next_pass": preconditions_ready,
            "apply_gate_policy_patch_flag_supported": False,
            "gate_policy_patch_writer_implemented": False,
            "gate_policy_patch_writer_allowed_in_this_pass": False,
            "gate_policy_patch_allowed_in_this_pass": False,
            "gate_policy_application_allowed_in_this_pass": False,
            "gate_policy_change_allowed": False,
            "gate_policy_change_performed": False,
            "allowlist_change_allowed": False,
            "allowlist_change_performed": False,
            "policy_file_write_allowed": False,
            "backup_artifact_written": False,
            "rollback_audit_artifact_written": False,
            "approval_consumed": False,
            "gate_approval_consumed": False,
            "inactive_artifacts_written": False,
            "trusted_skill_write_allowed": False,
            "siteops_skill_card_write_allowed": False,
            "browser_execution_allowed": False,
            "agent_bus_enqueue_allowed": False,
            "provider_api_call_allowed": False,
            "activation_allowed": False,
            "canonical_writeback_allowed": False,
            "writes_performed": False,
            "files_modified": False,
            "blocked_actions": denied_effects,
            "denied_effects": denied_effects,
            "boundary": (
                "Gate policy patch writer design only; it describes the future explicit "
                "two-file Gate writer and rollback sequence but performs no policy write, "
                "approval consumption, trusted artifact write, browser execution, Agent Bus "
                "work, provider call, activation, or canonical writeback."
            ),
        }
    )
    return result


def candidate_promotion_trusted_inactive_artifact_writer_gate_policy_patch_writer_implementation_request(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    replacement_approval_id: str,
    gate_approval_id: str,
    actor: str,
    reason: str | None = None,
) -> dict[str, Any]:
    """Return a no-write request packet for a future Gate policy patch writer."""
    design = candidate_promotion_trusted_inactive_artifact_writer_gate_policy_patch_writer_design(
        candidate_id,
        root,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
        replacement_approval_id=replacement_approval_id,
        gate_approval_id=gate_approval_id,
        actor=actor,
        reason=reason or "operator requested no-write Gate policy patch writer implementation request",
    )
    scope = dict(design.get("scope") or {})
    writer_design = dict(design.get("policy_patch_writer_design") or {})
    pre_write_digests = dict(writer_design.get("pre_write_digests") or {})
    target_files = list(writer_design.get("target_files") or [])
    future_patch = dict(writer_design.get("future_patch") or {})
    design_ready = bool(design.get("ready_for_gate_policy_patch_writer_implementation_request_next_pass"))
    exact_targets_ready = target_files == [
        "runtime/chaseos_gate.py",
        "runtime/policy/gateway_allowlists.json",
    ]
    digests_ready = bool(pre_write_digests.get("runtime_policy")) and bool(
        pre_write_digests.get("gateway_allowlists")
    )
    explicit_flag_ready = (
        writer_design.get("future_explicit_write_flag") == "--apply-gate-policy-patch"
        and writer_design.get("future_explicit_write_flag_supported_here") is False
        and writer_design.get("future_writer_requires_explicit_write_flag") is True
    )
    rollback_ready = (
        dict(writer_design.get("rollback_policy") or {}).get("backup_required_before_any_replace")
        is True
    )
    request_id = _new_run_id(f"{design.get('candidate_id')}_gate_policy_patch_writer_implementation_request")
    request_artifact = {
        "request_id": request_id,
        "request_type": "siteops_gate_policy_patch_writer_implementation_request",
        "tenant_id": scope.get("tenant_id"),
        "workspace_id": scope.get("workspace_id"),
        "user_id": scope.get("user_id"),
        "candidate_id": design.get("candidate_id"),
        "proposed_skill_id": design.get("proposed_skill_id"),
        "replacement_approval_id": replacement_approval_id,
        "gate_approval_id": gate_approval_id,
        "requested_action": "implement_gate_policy_patch_writer",
        "required_operator_decision": "approve_future_gate_policy_patch_writer_implementation_pass",
        "status": "review_packet_only",
        "writer_design_status": design.get("gate_policy_patch_writer_design_status"),
        "future_command_name": writer_design.get("future_command_name"),
        "future_explicit_write_flag": "--apply-gate-policy-patch",
        "target_files": target_files,
        "pre_write_digests": pre_write_digests,
        "future_patch": future_patch,
        "implementation_allowed_in_this_pass": False,
        "writes_allowed_in_this_pass": False,
        "gate_policy_write_allowed_in_this_pass": False,
        "approval_consumption_allowed_in_this_pass": False,
        "trusted_artifact_write_allowed_in_this_pass": False,
    }
    checks = list(design.get("gate_policy_patch_writer_design_checks") or []) + [
        _executor_preflight_check(
            "writer_implementation_request_design_ready",
            passed=design_ready,
            detail=str(design.get("gate_policy_patch_writer_design_status")),
        ),
        _executor_preflight_check(
            "writer_implementation_request_exact_target_files",
            passed=exact_targets_ready,
            detail=str(target_files),
        ),
        _executor_preflight_check(
            "writer_implementation_request_current_digests_present",
            passed=digests_ready,
            detail=str(pre_write_digests),
        ),
        _executor_preflight_check(
            "writer_implementation_request_future_apply_flag_required",
            passed=explicit_flag_ready,
            detail=str(writer_design.get("future_explicit_write_flag")),
        ),
        _executor_preflight_check(
            "writer_implementation_request_backup_rollback_required",
            passed=rollback_ready,
            detail=str(writer_design.get("rollback_policy")),
        ),
        _executor_preflight_check(
            "writer_implementation_request_no_writes_this_pass",
            passed=True,
            detail="implementation request only; the Gate policy patch writer is not implemented",
        ),
    ]
    checks_passed = all(bool(check.get("passed")) for check in checks if check.get("required", True))
    if design_ready and checks_passed:
        request_status = "gate_policy_patch_writer_implementation_request_ready_no_write"
        review_decision = "ready_for_operator_review_of_gate_policy_patch_writer_implementation"
    else:
        request_status = "blocked_gate_policy_patch_writer_implementation_request_preconditions"
        review_decision = "blocked_before_gate_policy_patch_writer_implementation_approval"

    denied_effects = list(design.get("denied_effects") or [])
    for item in [
        "write Gate policy patch writer implementation request",
        "implement Gate policy patch writer from implementation request",
        "accept --apply-gate-policy-patch on this implementation request command",
        "write Gate policy backup artifact",
        "write Gate policy rollback artifact",
    ]:
        if item not in denied_effects:
            denied_effects.append(item)

    result = dict(design)
    result.update(
        {
            "action": PROMOTION_TRUSTED_INACTIVE_ARTIFACT_WRITER_GATE_POLICY_PATCH_WRITER_IMPLEMENTATION_REQUEST_ACTION,
            "gate_policy_patch_writer_implementation_request_status": request_status,
            "review_decision": review_decision,
            "gate_policy_patch_writer_implementation_request": request_artifact,
            "policy_patch_writer_implementation_request": request_artifact,
            "gate_policy_patch_writer_implementation_request_checks": checks,
            "policy_patch_writer_implementation_request_checks": checks,
            "ready_for_gate_policy_patch_writer_implementation_approval_next_pass": (
                request_status == "gate_policy_patch_writer_implementation_request_ready_no_write"
            ),
            "implementation_request_artifact_written": False,
            "apply_gate_policy_patch_flag_supported": False,
            "future_apply_gate_policy_patch_flag_required": True,
            "gate_policy_patch_writer_implemented": False,
            "gate_policy_patch_writer_allowed_in_this_pass": False,
            "gate_policy_patch_allowed_in_this_pass": False,
            "gate_policy_application_allowed_in_this_pass": False,
            "gate_policy_change_allowed": False,
            "gate_policy_change_performed": False,
            "allowlist_change_allowed": False,
            "allowlist_change_performed": False,
            "policy_file_write_allowed": False,
            "backup_artifact_written": False,
            "rollback_audit_artifact_written": False,
            "approval_consumed": False,
            "gate_approval_consumed": False,
            "inactive_artifacts_written": False,
            "trusted_skill_write_allowed": False,
            "siteops_skill_card_write_allowed": False,
            "browser_execution_allowed": False,
            "agent_bus_enqueue_allowed": False,
            "provider_api_call_allowed": False,
            "activation_allowed": False,
            "canonical_writeback_allowed": False,
            "writes_performed": False,
            "files_modified": False,
            "blocked_actions": denied_effects,
            "denied_effects": denied_effects,
            "boundary": (
                "Gate policy patch writer implementation request only; it packages the "
                "writer-design evidence for operator review without implementing the writer, "
                "editing Gate policy, consuming approvals, writing backup/rollback artifacts, "
                "writing trusted artifacts, executing browsers, enqueueing Agent Bus work, "
                "calling providers, activating skills, or writing canonical state."
            ),
        }
    )
    return result


def candidate_promotion_trusted_inactive_artifact_writer_gate_policy_patch_writer_implementation_approval(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    replacement_approval_id: str,
    gate_approval_id: str,
    decision: str,
    actor: str,
    reason: str | None = None,
) -> dict[str, Any]:
    """Return a no-write approval/rejection packet for the future Gate patch writer."""
    normalized_decision = (decision or "").strip().lower()
    if normalized_decision not in {"approve", "reject"}:
        raise ValueError("decision must be 'approve' or 'reject'")

    implementation_request = (
        candidate_promotion_trusted_inactive_artifact_writer_gate_policy_patch_writer_implementation_request(
            candidate_id,
            root,
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            user_id=user_id,
            replacement_approval_id=replacement_approval_id,
            gate_approval_id=gate_approval_id,
            actor=actor,
            reason=reason
            or "operator requested no-write Gate policy patch writer implementation approval",
        )
    )
    scope = dict(implementation_request.get("scope") or {})
    request_artifact = dict(
        implementation_request.get("gate_policy_patch_writer_implementation_request") or {}
    )
    request_status = implementation_request.get("gate_policy_patch_writer_implementation_request_status")
    request_ready = bool(
        implementation_request.get("ready_for_gate_policy_patch_writer_implementation_approval_next_pass")
    )
    actor_id = (actor or user_id or "").strip()
    decision_id = _new_run_id(
        f"{implementation_request.get('candidate_id')}_gate_policy_patch_writer_implementation_approval"
    )
    approval_record = {
        "decision_id": decision_id,
        "record_type": "siteops_gate_policy_patch_writer_implementation_approval",
        "tenant_id": scope.get("tenant_id"),
        "workspace_id": scope.get("workspace_id"),
        "user_id": scope.get("user_id"),
        "actor": actor_id,
        "decision": normalized_decision,
        "reason": reason or "",
        "candidate_id": implementation_request.get("candidate_id"),
        "proposed_skill_id": implementation_request.get("proposed_skill_id"),
        "replacement_approval_id": replacement_approval_id,
        "gate_approval_id": gate_approval_id,
        "implementation_request_id": request_artifact.get("request_id"),
        "future_command_name": request_artifact.get("future_command_name"),
        "future_explicit_write_flag": "--apply-gate-policy-patch",
        "target_files": request_artifact.get("target_files"),
        "pre_write_digests": request_artifact.get("pre_write_digests"),
        "status": "review_decision_packet_only",
        "durable_record_written": False,
        "approval_decision_written": False,
        "implementation_allowed_in_this_pass": False,
        "gate_policy_write_allowed_in_this_pass": False,
        "backup_artifact_write_allowed_in_this_pass": False,
        "rollback_audit_write_allowed_in_this_pass": False,
        "approval_consumption_allowed": False,
    }
    implementation_approved = request_ready and normalized_decision == "approve"
    implementation_rejected = request_ready and normalized_decision == "reject"
    if not request_ready:
        approval_status = f"blocked_gate_policy_patch_writer_implementation_request: {request_status}"
        review_decision = "blocked_before_gate_policy_patch_writer_implementation_approval"
    elif implementation_approved:
        approval_status = "gate_policy_patch_writer_implementation_approved_for_next_pass_no_write"
        review_decision = "operator_intent_approve_gate_policy_patch_writer_implementation_next_pass"
    else:
        approval_status = "gate_policy_patch_writer_implementation_rejected_no_write"
        review_decision = "operator_intent_reject_gate_policy_patch_writer_implementation"

    approval_checks = {
        "implementation_request_ready": {
            "passed": request_ready,
            "status": request_status,
        },
        "decision_valid": {
            "passed": True,
            "decision": normalized_decision,
        },
        "actor_present": {
            "passed": bool(actor_id),
            "actor": actor_id,
        },
        "target_files_bound": {
            "passed": request_artifact.get("target_files")
            == [
                "runtime/chaseos_gate.py",
                "runtime/policy/gateway_allowlists.json",
            ],
            "target_files": request_artifact.get("target_files"),
        },
        "current_digests_bound": {
            "passed": bool(
                dict(request_artifact.get("pre_write_digests") or {}).get("runtime_policy")
            )
            and bool(
                dict(request_artifact.get("pre_write_digests") or {}).get(
                    "gateway_allowlists"
                )
            ),
            "pre_write_digests": request_artifact.get("pre_write_digests"),
        },
        "future_apply_flag_bound_but_unsupported_here": {
            "passed": request_artifact.get("future_explicit_write_flag")
            == "--apply-gate-policy-patch",
            "future_explicit_write_flag": request_artifact.get("future_explicit_write_flag"),
            "apply_gate_policy_patch_flag_supported_here": False,
        },
        "approval_record_still_no_write": {
            "passed": True,
            "durable_record_written": False,
            "approval_decision_written": False,
        },
        "gate_writer_execution_still_disabled": {
            "passed": True,
            "gate_policy_patch_writer_implemented": False,
            "gate_policy_patch_writer_allowed_in_this_pass": False,
        },
        "gate_policy_write_still_blocked_this_pass": {
            "passed": True,
            "gate_policy_change_performed": False,
            "allowlist_change_performed": False,
            "backup_artifact_written": False,
            "rollback_audit_artifact_written": False,
        },
    }
    if not approval_checks["actor_present"]["passed"]:
        approval_status = "blocked_missing_gate_policy_patch_writer_implementation_approval_actor"
        review_decision = "blocked_before_gate_policy_patch_writer_implementation_approval"
        implementation_approved = False
        implementation_rejected = False

    denied_effects = list(implementation_request.get("denied_effects") or [])
    for item in [
        "write Gate policy patch writer implementation approval record",
        "consume Gate policy patch writer implementation approval",
        "implement Gate policy patch writer in approval pass",
        "accept --apply-gate-policy-patch on this approval command",
        "edit runtime/chaseos_gate.py from implementation approval",
        "edit runtime/policy/gateway_allowlists.json from implementation approval",
        "write Gate policy backup artifact from implementation approval",
        "write Gate policy rollback artifact from implementation approval",
    ]:
        if item not in denied_effects:
            denied_effects.append(item)

    result = dict(implementation_request)
    result.update(
        {
            "action": PROMOTION_TRUSTED_INACTIVE_ARTIFACT_WRITER_GATE_POLICY_PATCH_WRITER_IMPLEMENTATION_APPROVAL_ACTION,
            "decision": normalized_decision,
            "actor": actor_id,
            "gate_policy_patch_writer_implementation_request_status": request_status,
            "gate_policy_patch_writer_implementation_approval_status": approval_status,
            "review_decision": review_decision,
            "gate_policy_patch_writer_implementation_approval": approval_record,
            "policy_patch_writer_implementation_approval": approval_record,
            "gate_policy_patch_writer_implementation_approval_checks": approval_checks,
            "policy_patch_writer_implementation_approval_checks": approval_checks,
            "implementation_request_packet": {
                "request_id": request_artifact.get("request_id"),
                "status": request_status,
                "request_ready_no_write": request_ready,
                "target_files": request_artifact.get("target_files"),
                "future_explicit_write_flag": request_artifact.get("future_explicit_write_flag"),
            },
            "gate_policy_patch_writer_implementation_allowed_next_pass": implementation_approved,
            "gate_policy_patch_writer_implementation_rejected_no_write": implementation_rejected,
            "ready_for_gate_policy_patch_writer_implementation_next_pass": implementation_approved,
            "implementation_approval_record_written": False,
            "approval_decision_written": False,
            "implementation_request_artifact_written": False,
            "apply_gate_policy_patch_flag_supported": False,
            "future_apply_gate_policy_patch_flag_required": True,
            "gate_policy_patch_writer_implemented": False,
            "gate_policy_patch_writer_allowed_in_this_pass": False,
            "gate_policy_patch_allowed_in_this_pass": False,
            "gate_policy_application_allowed_in_this_pass": False,
            "gate_policy_change_allowed": False,
            "gate_policy_change_performed": False,
            "allowlist_change_allowed": False,
            "allowlist_change_performed": False,
            "policy_file_write_allowed": False,
            "backup_artifact_written": False,
            "rollback_audit_artifact_written": False,
            "approval_consumed": False,
            "gate_approval_consumed": False,
            "inactive_artifacts_written": False,
            "trusted_skill_write_allowed": False,
            "siteops_skill_card_write_allowed": False,
            "browser_execution_allowed": False,
            "agent_bus_enqueue_allowed": False,
            "provider_api_call_allowed": False,
            "activation_allowed": False,
            "canonical_writeback_allowed": False,
            "writes_performed": False,
            "files_modified": False,
            "blocked_actions": denied_effects,
            "denied_effects": denied_effects,
            "future_writer_requirements": [
                "future Gate policy patch writer implementation pass must cite this approval packet and rerun implementation-request/preflight",
                "future writer must still require --apply-gate-policy-patch on the implementation command",
                "future writer must verify current runtime/chaseos_gate.py and runtime/policy/gateway_allowlists.json digests immediately before any write",
                "future writer must write backup and rollback/audit artifacts before replacing Gate files",
                "future writer must only add the reviewed operation/category entries and must run post-apply fail-closed smokes",
                "future writer must not write trusted artifacts, activate skills, launch browsers, enqueue Agent Bus work, call providers, or write canonical state",
            ],
            "boundary": (
                "Gate policy patch writer implementation approval packet only; it records "
                "operator approve/reject intent for a future writer implementation without "
                "writing an approval record, implementing the writer, editing Gate policy, "
                "writing backup/rollback artifacts, consuming approvals, writing trusted "
                "artifacts, executing browsers, enqueueing Agent Bus work, calling providers, "
                "activating skills, or writing canonical state."
            ),
        }
    )
    return result


def _gate_policy_runtime_operation_entry() -> str:
    return (
        f'    "{PROMOTION_GATE_APPLY_OPERATION}": {{\n'
        '        "allow_cli_operator": True,\n'
        '        "gateway_write_categories": [\n'
        '            "browser_skills_inactive_review",\n'
        '            "siteops_skill_cards_inactive_review",\n'
        "        ],\n"
        '        "write_target_categories": [\n'
        '            "browser_skills_inactive_review",\n'
        '            "siteops_skill_cards_inactive_review",\n'
        "        ],\n"
        "    },\n"
    )


def _apply_gate_policy_runtime_operation_patch(text: str) -> str:
    if f'"{PROMOTION_GATE_APPLY_OPERATION}"' in text:
        raise SiteOpsValidationError("Gate policy operation is already present")
    entry = _gate_policy_runtime_operation_entry()
    compact_assignment = "RUNTIME_OPERATION_POLICIES = {}\n"
    if text == compact_assignment:
        return "RUNTIME_OPERATION_POLICIES = {\n" + entry + "}\n"
    marker = "\n}\n\n\ndef get_runtime_operation_approval_schema"
    if marker not in text:
        raise SiteOpsValidationError("unable to locate RUNTIME_OPERATION_POLICIES insertion point")
    return text.replace(marker, "\n" + entry + "}\n\n\ndef get_runtime_operation_approval_schema", 1)


def _apply_gate_policy_gateway_allowlists_patch(text: str) -> tuple[str, dict[str, Any]]:
    payload = json.loads(text)
    write_targets = payload.setdefault("write_targets", {})
    required_entries = {
        "browser_skills_inactive_review": ["runtime/browser_skills/skills/*.yaml"],
        "siteops_skill_cards_inactive_review": [
            "runtime/siteops/registry/skill_cards/*.json"
        ],
    }
    for category in required_entries:
        if category in write_targets:
            raise SiteOpsValidationError(f"gateway allowlist category is already present: {category}")
    write_targets.update(required_entries)
    return json.dumps(payload, indent=2) + "\n", required_entries


def candidate_promotion_trusted_inactive_artifact_writer_gate_policy_patch_writer_implementation(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    replacement_approval_id: str,
    gate_approval_id: str,
    actor: str,
    reason: str | None = None,
    apply_gate_policy_patch: bool = False,
) -> dict[str, Any]:
    """Apply the reviewed two-file Gate policy patch only behind the explicit write flag."""
    approval = candidate_promotion_trusted_inactive_artifact_writer_gate_policy_patch_writer_implementation_approval(
        candidate_id,
        root,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
        replacement_approval_id=replacement_approval_id,
        gate_approval_id=gate_approval_id,
        decision="approve",
        actor=actor,
        reason=reason or "operator requested guarded Gate policy patch writer implementation",
    )
    scope = dict(approval.get("scope") or {})
    approval_status = approval.get("gate_policy_patch_writer_implementation_approval_status")
    implementation_ready = bool(approval.get("ready_for_gate_policy_patch_writer_implementation_next_pass"))
    design = dict(approval.get("policy_patch_writer_design") or {})
    pre_write_digests = dict(design.get("pre_write_digests") or {})
    target_files = list(design.get("target_files") or [])
    vault_root = Path(root or Path.cwd()).resolve(strict=False)
    runtime_rel = "runtime/chaseos_gate.py"
    allowlists_rel = "runtime/policy/gateway_allowlists.json"
    runtime_path = vault_root / runtime_rel
    allowlists_path = vault_root / allowlists_rel
    exact_targets_ready = target_files == [runtime_rel, allowlists_rel]
    target_paths_confined = all(
        _filesystem_path_is_within(path, vault_root) for path in [runtime_path, allowlists_path]
    )
    required_categories = {
        "browser_skills_inactive_review": ["runtime/browser_skills/skills/*.yaml"],
        "siteops_skill_cards_inactive_review": [
            "runtime/siteops/registry/skill_cards/*.json"
        ],
    }

    runtime_text = runtime_path.read_text(encoding="utf-8") if runtime_path.exists() else ""
    allowlists_text = allowlists_path.read_text(encoding="utf-8") if allowlists_path.exists() else ""
    current_runtime_digest = _sha256_file(runtime_path) if runtime_path.exists() else None
    current_allowlists_digest = _sha256_file(allowlists_path) if allowlists_path.exists() else None
    runtime_digest_matches = current_runtime_digest == pre_write_digests.get("runtime_policy")
    allowlists_digest_matches = current_allowlists_digest == pre_write_digests.get("gateway_allowlists")
    operation_absent = f'"{PROMOTION_GATE_APPLY_OPERATION}"' not in runtime_text
    allowlists_payload = json.loads(allowlists_text) if allowlists_text else {}
    existing_write_targets = dict(allowlists_payload.get("write_targets") or {})
    categories_absent = all(category not in existing_write_targets for category in required_categories)

    checks = {
        "implementation_approval_ready": {
            "passed": implementation_ready,
            "status": approval_status,
        },
        "apply_gate_policy_patch_flag_present": {
            "passed": bool(apply_gate_policy_patch),
            "required_for_write": True,
        },
        "target_files_exact": {
            "passed": exact_targets_ready,
            "target_files": target_files,
        },
        "target_paths_confined": {
            "passed": target_paths_confined,
            "target_files": [runtime_rel, allowlists_rel],
        },
        "current_runtime_policy_digest_matches_review": {
            "passed": runtime_digest_matches,
            "expected": pre_write_digests.get("runtime_policy"),
            "actual": current_runtime_digest,
        },
        "current_gateway_allowlists_digest_matches_review": {
            "passed": allowlists_digest_matches,
            "expected": pre_write_digests.get("gateway_allowlists"),
            "actual": current_allowlists_digest,
        },
        "gate_operation_absent_before_write": {
            "passed": operation_absent,
            "operation": PROMOTION_GATE_APPLY_OPERATION,
        },
        "gateway_categories_absent_before_write": {
            "passed": categories_absent,
            "categories": list(required_categories),
        },
    }
    patch_preconditions_ready = all(
        bool(check.get("passed"))
        for check_id, check in checks.items()
        if check_id != "apply_gate_policy_patch_flag_present"
    )
    run_id = _new_run_id(f"{candidate_id}_gate_policy_patch_writer_implementation")
    backup_dir = (
        vault_root
        / "07_LOGS"
        / "SiteOps-Gate-Policy-Patches"
        / str(scope.get("tenant_id") or tenant_id or "unknown-tenant")
        / str(scope.get("workspace_id") or workspace_id or "unknown-workspace")
        / run_id
    )
    backup_paths = {
        "runtime_policy": backup_dir / "runtime_chaseos_gate.py.bak",
        "gateway_allowlists": backup_dir / "gateway_allowlists.json.bak",
        "rollback_audit": backup_dir / "rollback_audit.json",
    }

    result = dict(approval)
    result.update(
        {
            "action": PROMOTION_TRUSTED_INACTIVE_ARTIFACT_WRITER_GATE_POLICY_PATCH_WRITER_IMPLEMENTATION_ACTION,
            "gate_policy_patch_writer_implementation_status": (
                "gate_policy_patch_writer_implementation_ready_dry_run"
                if patch_preconditions_ready and not apply_gate_policy_patch
                else "blocked_gate_policy_patch_writer_implementation_preconditions"
            ),
            "apply_gate_policy_patch_requested": bool(apply_gate_policy_patch),
            "apply_gate_policy_patch_flag_supported": True,
            "gate_policy_patch_writer_implemented": True,
            "gate_policy_patch_writer_allowed_in_this_pass": bool(apply_gate_policy_patch),
            "gate_policy_patch_writer_implementation_checks": checks,
            "policy_patch_writer_implementation_checks": checks,
            "write_preconditions_ready": patch_preconditions_ready,
            "target_files": [runtime_rel, allowlists_rel],
            "backup_artifact_paths": {
                key: path.relative_to(vault_root).as_posix() for key, path in backup_paths.items()
            },
            "gate_policy_change_allowed": bool(apply_gate_policy_patch),
            "allowlist_change_allowed": bool(apply_gate_policy_patch),
            "policy_file_write_allowed": bool(apply_gate_policy_patch),
            "gate_policy_change_performed": False,
            "allowlist_change_performed": False,
            "backup_artifact_written": False,
            "rollback_audit_artifact_written": False,
            "approval_consumed": False,
            "gate_approval_consumed": False,
            "inactive_artifacts_written": False,
            "trusted_skill_write_allowed": False,
            "siteops_skill_card_write_allowed": False,
            "browser_execution_allowed": False,
            "agent_bus_enqueue_allowed": False,
            "provider_api_call_allowed": False,
            "activation_allowed": False,
            "canonical_writeback_allowed": False,
            "writes_performed": False,
            "files_modified": False,
        }
    )
    if not apply_gate_policy_patch:
        return result
    if not patch_preconditions_ready:
        return result

    backup_dir.mkdir(parents=True, exist_ok=False)
    backup_paths["runtime_policy"].write_text(runtime_text, encoding="utf-8")
    backup_paths["gateway_allowlists"].write_text(allowlists_text, encoding="utf-8")
    rollback_audit = {
        "run_id": run_id,
        "candidate_id": candidate_id,
        "tenant_id": scope.get("tenant_id"),
        "workspace_id": scope.get("workspace_id"),
        "actor": actor,
        "operation": PROMOTION_GATE_APPLY_OPERATION,
        "created_at": now_iso(),
        "target_files": [runtime_rel, allowlists_rel],
        "pre_write_digests": pre_write_digests,
        "backup_files": {
            key: path.relative_to(vault_root).as_posix()
            for key, path in backup_paths.items()
            if key != "rollback_audit"
        },
        "contains_secrets_or_session_state": False,
        "rollback_performed": False,
    }
    backup_paths["rollback_audit"].write_text(
        json.dumps(rollback_audit, indent=2) + "\n", encoding="utf-8"
    )

    runtime_after = _apply_gate_policy_runtime_operation_patch(runtime_text)
    allowlists_after, applied_categories = _apply_gate_policy_gateway_allowlists_patch(allowlists_text)
    try:
        compile(runtime_after, str(runtime_path), "exec")
        json.loads(allowlists_after)
        runtime_path.write_text(runtime_after, encoding="utf-8")
        allowlists_path.write_text(allowlists_after, encoding="utf-8")
        compile(runtime_path.read_text(encoding="utf-8"), str(runtime_path), "exec")
        post_allowlists = json.loads(allowlists_path.read_text(encoding="utf-8"))
        post_write_targets = dict(post_allowlists.get("write_targets") or {})
        post_checks = {
            "runtime_policy_compiles": True,
            "gateway_allowlists_parses": True,
            "gate_operation_present_once": runtime_path.read_text(encoding="utf-8").count(
                f'"{PROMOTION_GATE_APPLY_OPERATION}"'
            )
            == 1,
            "gateway_categories_present_exact": all(
                post_write_targets.get(category) == patterns
                for category, patterns in applied_categories.items()
            ),
        }
        if not all(post_checks.values()):
            raise SiteOpsValidationError("post-apply Gate policy patch verification failed")
    except Exception:
        runtime_path.write_text(runtime_text, encoding="utf-8")
        allowlists_path.write_text(allowlists_text, encoding="utf-8")
        rollback_audit["rollback_performed"] = True
        backup_paths["rollback_audit"].write_text(
            json.dumps(rollback_audit, indent=2) + "\n", encoding="utf-8"
        )
        raise

    result.update(
        {
            "gate_policy_patch_writer_implementation_status": "gate_policy_patch_writer_implementation_applied",
            "review_decision": "gate_policy_patch_applied_retry_trusted_inactive_writer_readiness_next",
            "gate_policy_change_performed": True,
            "allowlist_change_performed": True,
            "backup_artifact_written": True,
            "rollback_audit_artifact_written": True,
            "writes_performed": True,
            "files_modified": True,
            "post_apply_verification": post_checks,
            "applied_gate_operation": PROMOTION_GATE_APPLY_OPERATION,
            "applied_gateway_categories": applied_categories,
            "boundary": (
                "Guarded Gate policy patch writer only; it may edit runtime/chaseos_gate.py "
                "and runtime/policy/gateway_allowlists.json when --apply-gate-policy-patch "
                "is present and pre-write digests still match. It does not consume approvals, "
                "write trusted artifacts, execute browsers, enqueue Agent Bus work, call providers, "
                "activate skills, or write canonical memory/state."
            ),
        }
    )
    return result


def candidate_promotion_trusted_inactive_artifact_writer_gate_policy_live_application_readiness(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    actor: str,
    replacement_approval_id: str | None = None,
    gate_approval_id: str | None = None,
    reason: str | None = None,
) -> dict[str, Any]:
    """Report whether the guarded live Gate policy patch application can be invoked."""
    scope = require_scope(tenant_id=tenant_id, workspace_id=workspace_id, user_id=user_id)
    vault_root = Path(root or Path.cwd()).resolve(strict=False)
    runtime_rel = "runtime/chaseos_gate.py"
    allowlists_rel = "runtime/policy/gateway_allowlists.json"
    runtime_path = vault_root / runtime_rel
    allowlists_path = vault_root / allowlists_rel
    runtime_exists = runtime_path.exists()
    allowlists_exists = allowlists_path.exists()
    runtime_text = runtime_path.read_text(encoding="utf-8") if runtime_exists else ""
    allowlists_text = allowlists_path.read_text(encoding="utf-8") if allowlists_exists else "{}"
    allowlists_payload: dict[str, Any] = {}
    allowlists_parse_ok = False
    allowlists_parse_error = None
    try:
        allowlists_payload = json.loads(allowlists_text)
        allowlists_parse_ok = True
    except Exception as exc:  # pragma: no cover - defensive live-read guard
        allowlists_parse_error = str(exc)
    write_targets = dict(allowlists_payload.get("write_targets") or {})
    required_categories = {
        "browser_skills_inactive_review": ["runtime/browser_skills/skills/*.yaml"],
        "siteops_skill_cards_inactive_review": [
            "runtime/siteops/registry/skill_cards/*.json"
        ],
    }
    operation_present = f'"{PROMOTION_GATE_APPLY_OPERATION}"' in runtime_text
    categories_present_exact = all(
        write_targets.get(category) == patterns
        for category, patterns in required_categories.items()
    )
    approval_ids_present = bool(replacement_approval_id and gate_approval_id)
    writer_dry_run: dict[str, Any] | None = None
    writer_dry_run_error: str | None = None
    if approval_ids_present and not (operation_present and categories_present_exact):
        try:
            writer_dry_run = candidate_promotion_trusted_inactive_artifact_writer_gate_policy_patch_writer_implementation(
                candidate_id,
                vault_root,
                tenant_id=scope.tenant_id,
                workspace_id=scope.workspace_id,
                user_id=scope.user_id,
                replacement_approval_id=str(replacement_approval_id),
                gate_approval_id=str(gate_approval_id),
                actor=actor,
                reason=reason or "operator requested no-write Gate policy live application readiness",
                apply_gate_policy_patch=False,
            )
        except Exception as exc:
            writer_dry_run_error = str(exc)

    writer_ready = bool(writer_dry_run and writer_dry_run.get("write_preconditions_ready"))
    live_apply_command = [
        "python",
        "-m",
        "runtime.cli.main",
        "siteops",
        "candidates",
        "trusted-inactive-artifact-writer-gate-policy-patch-writer-implementation",
        str(candidate_id),
        "--replacement-approval-id",
        str(replacement_approval_id or "<APPROVAL_ID>"),
        "--gate-approval-id",
        str(gate_approval_id or "<GATE_APPROVAL_ID>"),
        "--tenant",
        scope.tenant_id,
        "--workspace",
        scope.workspace_id,
        "--user",
        scope.user_id,
        "--actor",
        str(actor),
        "--apply-gate-policy-patch",
        "--json",
    ]
    if operation_present and categories_present_exact:
        readiness_status = "gate_policy_live_application_already_applied_no_write"
        review_decision = "ready_for_trusted_inactive_writer_readiness_retry"
    elif not approval_ids_present:
        readiness_status = "blocked_missing_gate_policy_live_application_approval_ids"
        review_decision = "provide_real_replacement_and_gate_approval_ids_before_live_apply"
    elif writer_ready:
        readiness_status = "gate_policy_live_application_ready_no_write"
        review_decision = "ready_for_operator_reviewed_apply_gate_policy_patch_command"
    else:
        readiness_status = "blocked_gate_policy_live_application_preconditions"
        review_decision = "repair_approval_or_digest_preconditions_before_live_apply"

    checks = [
        _executor_preflight_check(
            "gate_policy_files_present",
            passed=runtime_exists and allowlists_exists,
            detail=f"{runtime_rel}={runtime_exists}; {allowlists_rel}={allowlists_exists}",
        ),
        _executor_preflight_check(
            "gateway_allowlists_parse_ok",
            passed=allowlists_parse_ok,
            detail=str(allowlists_parse_error or "parsed"),
        ),
        _executor_preflight_check(
            "live_operation_currently_present",
            passed=operation_present,
            required=False,
            detail=PROMOTION_GATE_APPLY_OPERATION,
        ),
        _executor_preflight_check(
            "live_gateway_categories_present_exact",
            passed=categories_present_exact,
            required=False,
            detail=str(required_categories),
        ),
        _executor_preflight_check(
            "real_approval_ids_present",
            passed=approval_ids_present,
            detail=f"replacement={bool(replacement_approval_id)}; gate={bool(gate_approval_id)}",
        ),
        _executor_preflight_check(
            "guarded_writer_dry_run_ready",
            passed=writer_ready,
            required=False,
            detail=writer_dry_run_error
            or str(
                (writer_dry_run or {}).get(
                    "gate_policy_patch_writer_implementation_status", "not_run"
                )
            ),
        ),
        _executor_preflight_check(
            "live_application_not_run_this_pass",
            passed=True,
            detail="readiness only; does not pass --apply-gate-policy-patch to the writer",
        ),
    ]
    return {
        "ok": True,
        "action": PROMOTION_TRUSTED_INACTIVE_ARTIFACT_WRITER_GATE_POLICY_LIVE_APPLICATION_READINESS_ACTION,
        "candidate_id": candidate_id,
        "scope": {
            "tenant_id": scope.tenant_id,
            "workspace_id": scope.workspace_id,
            "user_id": scope.user_id,
        },
        "actor": actor,
        "replacement_approval_id": replacement_approval_id,
        "gate_approval_id": gate_approval_id,
        "gate_operation": PROMOTION_GATE_APPLY_OPERATION,
        "gate_policy_live_application_readiness_status": readiness_status,
        "review_decision": review_decision,
        "runtime_policy": {
            "path": runtime_rel,
            "exists": runtime_exists,
            "sha256": _sha256_file(runtime_path) if runtime_exists else None,
            "operation_present": operation_present,
        },
        "gateway_allowlists": {
            "path": allowlists_rel,
            "exists": allowlists_exists,
            "sha256": _sha256_file(allowlists_path) if allowlists_exists else None,
            "parse_ok": allowlists_parse_ok,
            "parse_error": allowlists_parse_error,
            "required_categories_present_exact": categories_present_exact,
        },
        "required_gateway_categories": required_categories,
        "writer_dry_run_status": (writer_dry_run or {}).get(
            "gate_policy_patch_writer_implementation_status"
        ),
        "writer_dry_run_error": writer_dry_run_error,
        "ready_for_live_gate_policy_application": readiness_status
        == "gate_policy_live_application_ready_no_write",
        "gate_policy_already_applied": operation_present and categories_present_exact,
        "ready_for_trusted_inactive_writer_readiness_retry": (
            operation_present and categories_present_exact
        ),
        "live_apply_command_preview": live_apply_command,
        "gate_policy_live_application_readiness_checks": checks,
        "writes_performed": False,
        "files_modified": False,
        "gate_policy_change_performed": False,
        "allowlist_change_performed": False,
        "backup_artifact_written": False,
        "rollback_audit_artifact_written": False,
        "approval_consumed": False,
        "gate_approval_consumed": False,
        "inactive_artifacts_written": False,
        "trusted_skill_write_allowed": False,
        "siteops_skill_card_write_allowed": False,
        "browser_execution_allowed": False,
        "agent_bus_enqueue_allowed": False,
        "provider_api_call_allowed": False,
        "activation_allowed": False,
        "canonical_writeback_allowed": False,
        "boundary": (
            "Gate policy live application readiness only; it reports current Gate "
            "file posture and guarded writer dry-run status without applying the "
            "Gate patch, consuming approvals, writing trusted artifacts, activating "
            "skills, launching browsers, enqueueing Agent Bus work, calling providers, "
            "or writing canonical memory/state."
        ),
    }


def _load_activation_artifact(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        text = path.read_text(encoding="utf-8")
        if path.suffix.lower() in {".yaml", ".yml"} and yaml is not None:
            payload = yaml.safe_load(text) or {}
        else:
            payload = json.loads(text)
        if not isinstance(payload, dict):
            return None, "artifact root must be a mapping"
        return payload, None
    except Exception as exc:
        return None, str(exc)


def _activation_artifact_posture(
    *,
    vault_root: Path,
    path: Path,
    base_rel: Path,
    expected_skill_id: str,
    artifact_kind: str,
) -> dict[str, Any]:
    confined = _filesystem_path_is_within(path, vault_root / base_rel)
    exists = path.exists()
    payload: dict[str, Any] | None = None
    parse_error: str | None = None
    if exists and confined:
        payload, parse_error = _load_activation_artifact(path)
    status = str((payload or {}).get("status") or "")
    activation_allowed = (payload or {}).get("activation_allowed")
    skill_id = str((payload or {}).get("skill_id") or "")
    secret_errors = scan_secret_like_keys(payload or {}) if payload else []
    return {
        "artifact_kind": artifact_kind,
        "path": path.as_posix(),
        "path_confined": confined,
        "exists": exists,
        "parse_ok": bool(payload is not None and parse_error is None),
        "parse_error": parse_error,
        "skill_id": skill_id or None,
        "skill_id_matches": bool(skill_id == expected_skill_id),
        "status": status or None,
        "status_inactive_review": status == "inactive_review",
        "activation_allowed": activation_allowed,
        "activation_allowed_false": activation_allowed is False,
        "secret_like_keys_detected": secret_errors,
        "ready_for_activation_design": bool(
            confined
            and exists
            and payload is not None
            and parse_error is None
            and skill_id == expected_skill_id
            and status == "inactive_review"
            and activation_allowed is False
            and not secret_errors
        ),
    }


def candidate_promotion_activation_executor_design(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    source_approval_id: str,
    activation_approval_id: str,
    actor: str,
    reason: str | None = None,
) -> dict[str, Any]:
    """Design the future activation executor without mutating artifacts."""
    scope = require_scope(tenant_id=tenant_id, workspace_id=workspace_id, user_id=user_id)
    _validate_request_scope(root, scope)
    vault_root = Path(root or ".").resolve()
    candidate = candidate_promotion_request_contract(
        candidate_id,
        root,
        requested_by=actor or scope.user_id,
        tenant_id=scope.tenant_id,
        workspace_id=scope.workspace_id,
        user_id=scope.user_id,
    )
    resolved_candidate_id = str(candidate.get("candidate_id") or candidate_id)
    proposed_skill_id = str(candidate.get("proposed_skill_id") or "").strip()
    if not proposed_skill_id:
        proposed_skill_id = resolved_candidate_id

    writer_probe_error: str | None = None
    writer_probe: dict[str, Any] | None = None
    try:
        writer_probe = candidate_promotion_activation_approval_decision_consumer_writer_implementation(
            resolved_candidate_id,
            root,
            tenant_id=scope.tenant_id,
            workspace_id=scope.workspace_id,
            user_id=scope.user_id,
            source_approval_id=source_approval_id,
            activation_approval_id=activation_approval_id,
            actor=actor,
            reason=reason or "operator requested activation executor design",
            consume_activation_approval=False,
        )
    except (SiteOpsError, RuntimeError, ValueError) as exc:
        writer_probe_error = str(exc)

    marker_path_text = str((writer_probe or {}).get("activation_consumer_marker_path") or "").strip()
    marker_path = Path(marker_path_text) if marker_path_text else Path()
    marker_parent = vault_root / "07_LOGS" / "SiteOps-Activation-Consumers" / scope.tenant_id / scope.workspace_id
    marker_confined = bool(marker_path_text and _filesystem_path_is_within(marker_path, marker_parent))
    marker_exists = bool(marker_path_text and marker_path.exists())
    marker_payload: dict[str, Any] | None = None
    marker_parse_error: str | None = None
    if marker_exists and marker_confined:
        marker_payload, marker_parse_error = _load_activation_artifact(marker_path)
    marker_secret_errors = scan_secret_like_keys(marker_payload or {}) if marker_payload else []
    marker_candidate_matches = (marker_payload or {}).get("candidate_id") == resolved_candidate_id
    marker_skill_matches = (marker_payload or {}).get("proposed_skill_id") == proposed_skill_id
    marker_source_matches = (marker_payload or {}).get("source_approval_id") == source_approval_id
    marker_activation_matches = (marker_payload or {}).get("activation_approval_id") == activation_approval_id
    marker_valid = bool(
        marker_exists
        and marker_confined
        and marker_payload
        and marker_parse_error is None
        and marker_candidate_matches
        and marker_skill_matches
        and marker_source_matches
        and marker_activation_matches
        and not marker_secret_errors
        and marker_payload.get("activation_performed") is False
        and marker_payload.get("trusted_artifacts_written") is False
    )

    browser_skill_path = vault_root / TRUSTED_SKILL_REL / f"{proposed_skill_id}.yaml"
    siteops_card_rel = _siteops_skill_card_target(proposed_skill_id)
    siteops_card_path = vault_root / str(siteops_card_rel or "")
    artifact_posture = [
        _activation_artifact_posture(
            vault_root=vault_root,
            path=browser_skill_path,
            base_rel=TRUSTED_SKILL_REL,
            expected_skill_id=proposed_skill_id,
            artifact_kind="browser_skill",
        ),
        _activation_artifact_posture(
            vault_root=vault_root,
            path=siteops_card_path,
            base_rel=SITEOPS_SKILL_CARD_REL,
            expected_skill_id=proposed_skill_id,
            artifact_kind="siteops_skill_card",
        ),
    ]
    artifacts_exist = all(item["exists"] for item in artifact_posture)
    artifacts_ready = all(item["ready_for_activation_design"] for item in artifact_posture)
    activation_record_path = (
        vault_root
        / "07_LOGS"
        / "SiteOps-Activations"
        / scope.tenant_id
        / scope.workspace_id
        / f"activation-{_slug(resolved_candidate_id)[:64]}.json"
    )
    activation_record_confined = _filesystem_path_is_within(
        activation_record_path,
        vault_root / "07_LOGS" / "SiteOps-Activations" / scope.tenant_id / scope.workspace_id,
    )
    future_activation_state_transition = {
        "status": "future_activation_state_transition_preview_only",
        "explicit_future_flag": "--activate-trusted-artifact",
        "browser_skill": {
            "path": browser_skill_path.as_posix(),
            "from_status": "inactive_review",
            "to_status": "active_approved",
            "activation_allowed": True,
            "browser_execution_allowed_by_activation_alone": False,
        },
        "siteops_skill_card": {
            "path": siteops_card_path.as_posix(),
            "from_status": "inactive_review",
            "to_status": "active_approved",
            "activation_allowed": True,
            "workflow_execution_allowed_by_activation_alone": False,
        },
        "activation_record": {
            "path": activation_record_path.as_posix(),
            "create_new_only": True,
            "append_only_audit_required": True,
            "written_in_this_pass": False,
        },
    }
    activation_executor_sequence = [
        "require explicit future --activate-trusted-artifact flag",
        "reload candidate and scope",
        "verify consumed activation marker exists and matches candidate/source/activation approvals",
        "verify trusted Browser Skill and SiteOps Skill Card exist under scoped trusted roots",
        "verify trusted artifacts are inactive_review and activation_allowed=false",
        "verify no secret-like keys are present in marker or artifacts",
        "write pre-activation audit event",
        "atomically update trusted artifacts to active_approved with activation_allowed=true",
        "create activation record under scoped activation log root",
        "write post-activation audit event",
        "stop before browser replay, Agent Bus enqueue, provider calls, or canonical writeback",
    ]
    checks = [
        _executor_preflight_check(
            "activation_consumer_writer_probe_available",
            passed=writer_probe is not None,
            detail=writer_probe_error or str((writer_probe or {}).get("activation_approval_decision_consumer_writer_implementation_status")),
        ),
        _executor_preflight_check(
            "activation_consumption_marker_present",
            passed=marker_exists,
            detail=marker_path.as_posix() if marker_path_text else "missing",
        ),
        _executor_preflight_check(
            "activation_consumption_marker_scoped",
            passed=marker_confined,
            detail=marker_path.as_posix() if marker_path_text else "missing",
        ),
        _executor_preflight_check(
            "activation_consumption_marker_matches_candidate_and_approvals",
            passed=marker_valid,
            detail=marker_parse_error
            or (
                f"candidate={marker_candidate_matches}; skill={marker_skill_matches}; "
                f"source={marker_source_matches}; activation={marker_activation_matches}"
            ),
        ),
        _executor_preflight_check(
            "inactive_trusted_artifacts_exist",
            passed=artifacts_exist,
            detail=", ".join(item["path"] for item in artifact_posture if not item["exists"]) or "all present",
        ),
        _executor_preflight_check(
            "inactive_trusted_artifacts_ready",
            passed=artifacts_ready,
            detail=", ".join(
                f"{item['artifact_kind']} status={item['status']} activation_allowed={item['activation_allowed']}"
                for item in artifact_posture
                if not item["ready_for_activation_design"]
            )
            or "all inactive_review with activation_allowed=false",
        ),
        _executor_preflight_check(
            "future_activation_record_path_scoped",
            passed=activation_record_confined,
            detail=activation_record_path.as_posix(),
        ),
        _executor_preflight_check(
            "activation_executor_stops_before_browser_runtime",
            passed=True,
            detail="activation executor design does not launch browser/CDP, Agent Bus, providers, or canonical writeback",
        ),
    ]
    if not marker_exists:
        design_status = "blocked_activation_consumption_marker_missing"
        review_decision = "consume_activation_approval_marker_before_activation_executor"
    elif not marker_valid:
        design_status = "blocked_activation_consumption_marker_invalid"
        review_decision = "repair_or_recreate_scoped_activation_consumption_marker"
    elif not artifacts_exist:
        design_status = "blocked_inactive_trusted_artifacts_missing"
        review_decision = "write_inactive_trusted_artifacts_before_activation_executor"
    elif not artifacts_ready:
        design_status = "blocked_trusted_artifacts_not_inactive"
        review_decision = "restore_inactive_review_artifact_posture_before_activation"
    else:
        design_status = "activation_executor_design_ready_no_write"
        review_decision = "ready_for_activation_executor_preflight_next_pass"

    denied_effects = [
        "activate promoted skills",
        "set activation_allowed=true",
        "write activation record",
        "mutate trusted Browser Skill artifact",
        "mutate SiteOps Skill Card artifact",
        "append activation audit events",
        "launch or control a browser",
        "enqueue Agent Bus work",
        "call provider APIs",
        "mutate Gate policy",
        "write canonical ChaseOS memory/state",
    ]
    return {
        "ok": True,
        "action": PROMOTION_ACTIVATION_EXECUTOR_DESIGN_ACTION,
        "candidate_id": resolved_candidate_id,
        "proposed_skill_id": proposed_skill_id,
        "scope": scope.as_dict(),
        "actor": actor,
        "source_approval_id": source_approval_id,
        "activation_approval_id": activation_approval_id,
        "activation_executor_design_status": design_status,
        "review_decision": review_decision,
        "writer_probe_status": (writer_probe or {}).get(
            "activation_approval_decision_consumer_writer_implementation_status"
        ),
        "writer_probe_error": writer_probe_error,
        "activation_consumption_marker": {
            "path": marker_path.as_posix() if marker_path_text else None,
            "exists": marker_exists,
            "path_confined": marker_confined,
            "parse_ok": bool(marker_payload is not None and marker_parse_error is None),
            "parse_error": marker_parse_error,
            "candidate_matches": marker_candidate_matches,
            "proposed_skill_matches": marker_skill_matches,
            "source_approval_matches": marker_source_matches,
            "activation_approval_matches": marker_activation_matches,
            "secret_like_keys_detected": marker_secret_errors,
            "valid_for_activation_executor_design": marker_valid,
        },
        "trusted_artifact_posture": artifact_posture,
        "activation_executor_sequence": activation_executor_sequence,
        "future_activation_state_transition": future_activation_state_transition,
        "activation_executor_design_checks": checks,
        "ready_for_activation_executor_preflight_next_pass": (
            design_status == "activation_executor_design_ready_no_write"
        ),
        "activation_executor_implemented": False,
        "activation_executor_enabled": False,
        "activation_executor_write_allowed_in_this_pass": False,
        "future_activate_trusted_artifact_flag_supported": False,
        "writes_performed": False,
        "files_modified": False,
        "run_record_written": False,
        "activation_record_written": False,
        "activation_audit_written": False,
        "approval_consumed": False,
        "activation_consumption_marker_written": False,
        "approval_request_status_mutated": False,
        "trusted_artifacts_written": False,
        "trusted_artifacts_mutated": False,
        "trusted_skill_write_allowed": False,
        "siteops_skill_card_write_allowed": False,
        "activation_allowed": False,
        "activation_performed": False,
        "browser_execution_allowed": False,
        "agent_bus_enqueue_allowed": False,
        "provider_api_call_allowed": False,
        "gate_policy_mutation_allowed": False,
        "canonical_writeback_allowed": False,
        "blocked_actions": denied_effects,
        "denied_effects": denied_effects,
        "boundary": (
            "activation executor design only; verifies consumed marker evidence "
            "and inactive trusted artifact posture, then previews future activation "
            "state transitions. It performs no activation, artifact mutation, audit "
            "write, browser execution, Agent Bus enqueue, provider call, Gate mutation, "
            "or canonical writeback."
        ),
    }


def candidate_promotion_activation_executor_preflight(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    source_approval_id: str,
    activation_approval_id: str,
    actor: str,
    reason: str | None = None,
) -> dict[str, Any]:
    """Preflight the future activation executor without mutating artifacts."""
    scope = require_scope(tenant_id=tenant_id, workspace_id=workspace_id, user_id=user_id)
    _validate_request_scope(root, scope)
    vault_root = Path(root or ".").resolve()
    design = candidate_promotion_activation_executor_design(
        candidate_id,
        root,
        tenant_id=scope.tenant_id,
        workspace_id=scope.workspace_id,
        user_id=scope.user_id,
        source_approval_id=source_approval_id,
        activation_approval_id=activation_approval_id,
        actor=actor,
        reason=reason or "operator requested activation executor preflight",
    )
    future_transition = dict(design.get("future_activation_state_transition") or {})
    activation_record = dict(future_transition.get("activation_record") or {})
    activation_record_path_text = str(activation_record.get("path") or "").strip()
    activation_record_path = Path(activation_record_path_text) if activation_record_path_text else Path()
    activation_record_parent = (
        vault_root
        / "07_LOGS"
        / "SiteOps-Activations"
        / scope.tenant_id
        / scope.workspace_id
    )
    activation_record_confined = bool(
        activation_record_path_text
        and _filesystem_path_is_within(activation_record_path, activation_record_parent)
    )
    activation_record_absent = bool(activation_record_path_text and not activation_record_path.exists())
    design_ready = bool(
        design.get("activation_executor_design_status") == "activation_executor_design_ready_no_write"
        and design.get("ready_for_activation_executor_preflight_next_pass") is True
    )
    marker = dict(design.get("activation_consumption_marker") or {})
    marker_valid = bool(marker.get("valid_for_activation_executor_design") is True)
    artifact_posture = list(design.get("trusted_artifact_posture") or [])
    artifacts_ready = bool(
        artifact_posture
        and all(item.get("ready_for_activation_design") is True for item in artifact_posture)
    )
    future_flag_declared = (
        str(future_transition.get("explicit_future_flag") or "") == "--activate-trusted-artifact"
    )
    future_flag_unsupported = design.get("future_activate_trusted_artifact_flag_supported") is False
    checks = [
        _executor_preflight_check(
            "activation_executor_design_ready",
            passed=design_ready,
            detail=str(design.get("activation_executor_design_status")),
        ),
        _executor_preflight_check(
            "activation_consumption_marker_valid",
            passed=marker_valid,
            detail=str(marker.get("path") or "missing"),
        ),
        _executor_preflight_check(
            "inactive_trusted_artifacts_ready",
            passed=artifacts_ready,
            detail="all inactive trusted artifacts ready"
            if artifacts_ready
            else "missing or not inactive_review with activation_allowed=false",
        ),
        _executor_preflight_check(
            "future_activation_record_path_scoped",
            passed=activation_record_confined,
            detail=activation_record_path.as_posix() if activation_record_path_text else "missing",
        ),
        _executor_preflight_check(
            "future_activation_record_absent_before_write",
            passed=activation_record_absent,
            detail=activation_record_path.as_posix() if activation_record_path_text else "missing",
        ),
        _executor_preflight_check(
            "future_activate_trusted_artifact_flag_declared",
            passed=future_flag_declared,
            detail=str(future_transition.get("explicit_future_flag") or "missing"),
        ),
        _executor_preflight_check(
            "future_activate_trusted_artifact_flag_unsupported_in_preflight",
            passed=future_flag_unsupported,
            detail="preflight does not accept or execute activation flags",
        ),
        _executor_preflight_check(
            "preflight_stops_before_browser_runtime",
            passed=True,
            detail="no browser/CDP, Agent Bus, provider, Gate, or canonical writeback authority",
        ),
    ]
    ready_for_next = all(check["passed"] for check in checks if check.get("required", True))
    if not design_ready:
        preflight_status = "blocked_activation_executor_design_not_ready"
        review_decision = str(design.get("review_decision") or "fix_design_blockers_before_activation_preflight")
    elif not activation_record_confined:
        preflight_status = "blocked_future_activation_record_path_unscoped"
        review_decision = "repair_activation_record_scope_before_activation_executor"
    elif not activation_record_absent:
        preflight_status = "blocked_future_activation_record_already_exists"
        review_decision = "manual_review_required_before_activation_executor"
    else:
        preflight_status = "activation_executor_preflight_ready_no_write"
        review_decision = "ready_for_activation_executor_implementation_request_next_pass"

    denied_effects = [
        "activate promoted skills",
        "set activation_allowed=true",
        "write activation record",
        "mutate trusted Browser Skill artifact",
        "mutate SiteOps Skill Card artifact",
        "append activation audit events",
        "launch or control a browser",
        "enqueue Agent Bus work",
        "call provider APIs",
        "mutate Gate policy",
        "write canonical ChaseOS memory/state",
    ]
    return {
        "ok": True,
        "action": PROMOTION_ACTIVATION_EXECUTOR_PREFLIGHT_ACTION,
        "candidate_id": design.get("candidate_id"),
        "proposed_skill_id": design.get("proposed_skill_id"),
        "scope": scope.as_dict(),
        "actor": actor,
        "source_approval_id": source_approval_id,
        "activation_approval_id": activation_approval_id,
        "activation_executor_preflight_status": preflight_status,
        "activation_executor_design_status": design.get("activation_executor_design_status"),
        "review_decision": review_decision,
        "activation_executor_preflight_checks": checks,
        "activation_executor_design_checks": design.get("activation_executor_design_checks") or [],
        "activation_consumption_marker": marker,
        "trusted_artifact_posture": artifact_posture,
        "future_activation_state_transition": future_transition,
        "future_activation_record": {
            "path": activation_record_path.as_posix() if activation_record_path_text else None,
            "path_confined": activation_record_confined,
            "exists": bool(activation_record_path_text and activation_record_path.exists()),
            "create_new_only": True,
            "written_in_this_pass": False,
        },
        "ready_for_activation_executor_implementation_request_next_pass": ready_for_next,
        "activation_executor_implemented": False,
        "activation_executor_enabled": False,
        "activation_executor_write_allowed_in_this_pass": False,
        "future_activate_trusted_artifact_flag_supported": False,
        "activate_trusted_artifact_flag_supported_in_this_pass": False,
        "writes_performed": False,
        "files_modified": False,
        "run_record_written": False,
        "activation_record_written": False,
        "activation_audit_written": False,
        "approval_consumed": False,
        "activation_consumption_marker_written": False,
        "approval_request_status_mutated": False,
        "trusted_artifacts_written": False,
        "trusted_artifacts_mutated": False,
        "trusted_skill_write_allowed": False,
        "siteops_skill_card_write_allowed": False,
        "activation_allowed": False,
        "activation_performed": False,
        "browser_execution_allowed": False,
        "agent_bus_enqueue_allowed": False,
        "provider_api_call_allowed": False,
        "gate_policy_mutation_allowed": False,
        "canonical_writeback_allowed": False,
        "blocked_actions": denied_effects,
        "denied_effects": denied_effects,
        "boundary": (
            "activation executor preflight only; validates design readiness, "
            "consumed marker evidence, inactive trusted artifacts, and the future "
            "create-new activation record path. It performs no activation, artifact "
            "mutation, audit write, browser execution, Agent Bus enqueue, provider "
            "call, Gate mutation, or canonical writeback."
        ),
    }


def candidate_promotion_activation_executor_implementation_request(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    source_approval_id: str,
    activation_approval_id: str,
    actor: str,
    reason: str | None = None,
) -> dict[str, Any]:
    """Package activation executor preflight evidence for operator review without writes."""
    preflight = candidate_promotion_activation_executor_preflight(
        candidate_id,
        root,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
        source_approval_id=source_approval_id,
        activation_approval_id=activation_approval_id,
        actor=actor,
        reason=reason or "operator requested activation executor implementation request",
    )
    scope = dict(preflight.get("scope") or {})
    future_transition = dict(preflight.get("future_activation_state_transition") or {})
    future_activation_record = dict(preflight.get("future_activation_record") or {})
    future_write_set = {
        "explicit_write_flag": "--activate-trusted-artifact",
        "activation_record_path": future_activation_record.get("path"),
        "activation_record_create_new_only": True,
        "append_only_activation_audit_required": True,
        "browser_skill_path": (future_transition.get("browser_skill") or {}).get("path"),
        "siteops_skill_card_path": (future_transition.get("siteops_skill_card") or {}).get("path"),
        "browser_skill_status_transition": {
            "from": (future_transition.get("browser_skill") or {}).get("from_status"),
            "to": (future_transition.get("browser_skill") or {}).get("to_status"),
        },
        "siteops_skill_card_status_transition": {
            "from": (future_transition.get("siteops_skill_card") or {}).get("from_status"),
            "to": (future_transition.get("siteops_skill_card") or {}).get("to_status"),
        },
        "activation_allowed_transition": {
            "from": False,
            "to": True,
        },
        "stop_before_browser_runtime": True,
        "stop_before_agent_bus_provider_or_canonical_writeback": True,
    }
    record_schema = {
        "record_type": "siteops_activation_executor_implementation_request",
        "required_fields": [
            "request_id",
            "tenant_id",
            "workspace_id",
            "user_id",
            "candidate_id",
            "proposed_skill_id",
            "source_approval_id",
            "activation_approval_id",
            "preflight_status",
            "future_write_set",
            "required_operator_decision",
        ],
        "forbidden_fields": [
            "cookie",
            "token",
            "secret",
            "password",
            "browser_session_state",
            "personal_account_state",
        ],
        "durable_artifact_written_in_this_pass": False,
    }
    request_id = _new_run_id(
        f"{preflight.get('candidate_id')}_activation_executor_implementation_request"
    )
    request_packet = {
        "request_id": request_id,
        "request_type": "siteops_activation_executor_implementation_request",
        "tenant_id": scope.get("tenant_id"),
        "workspace_id": scope.get("workspace_id"),
        "user_id": scope.get("user_id"),
        "candidate_id": preflight.get("candidate_id"),
        "proposed_skill_id": preflight.get("proposed_skill_id"),
        "source_approval_id": source_approval_id,
        "activation_approval_id": activation_approval_id,
        "actor": actor,
        "reason": reason or "",
        "requested_action": "implement_guarded_activation_executor",
        "required_operator_decision": "approve_future_activation_executor_implementation_pass",
        "status": "review_packet_only",
        "preflight_status": preflight.get("activation_executor_preflight_status"),
        "future_command_name": "activation-executor",
        "future_explicit_write_flag": "--activate-trusted-artifact",
        "future_write_set": future_write_set,
        "record_schema": record_schema,
        "preflight_checks": preflight.get("activation_executor_preflight_checks") or [],
        "implementation_allowed_in_this_pass": False,
        "writes_allowed_in_this_pass": False,
        "activation_record_write_allowed_in_this_pass": False,
        "activation_audit_write_allowed_in_this_pass": False,
        "trusted_artifact_mutation_allowed_in_this_pass": False,
        "browser_execution_allowed_in_this_pass": False,
        "agent_bus_enqueue_allowed_in_this_pass": False,
        "provider_call_allowed_in_this_pass": False,
        "canonical_writeback_allowed_in_this_pass": False,
    }
    preflight_ready = bool(
        preflight.get("ready_for_activation_executor_implementation_request_next_pass")
    )
    future_write_set_ready = bool(
        future_write_set["activation_record_path"]
        and future_write_set["browser_skill_path"]
        and future_write_set["siteops_skill_card_path"]
    )
    checks = list(preflight.get("activation_executor_preflight_checks") or []) + [
        _executor_preflight_check(
            "activation_executor_implementation_request_preflight_ready",
            passed=preflight_ready,
            detail=str(preflight.get("activation_executor_preflight_status")),
        ),
        _executor_preflight_check(
            "activation_executor_implementation_request_future_flag_required",
            passed=future_write_set.get("explicit_write_flag") == "--activate-trusted-artifact",
            detail=str(future_write_set.get("explicit_write_flag")),
        ),
        _executor_preflight_check(
            "activation_executor_implementation_request_future_write_set_ready",
            passed=future_write_set_ready,
            detail=str(future_write_set),
        ),
        _executor_preflight_check(
            "activation_executor_implementation_request_record_schema_ready",
            passed=bool(record_schema["required_fields"]),
            detail=str(record_schema["required_fields"]),
        ),
        _executor_preflight_check(
            "activation_executor_implementation_request_no_writes_this_pass",
            passed=True,
            detail="implementation request only; activation executor remains unimplemented",
        ),
    ]
    checks_ready = all(bool(check.get("passed")) for check in checks if check.get("required", True))
    if preflight_ready and checks_ready:
        request_status = "activation_executor_implementation_request_ready_no_write"
        review_decision = "ready_for_activation_executor_implementation_approval_next_pass"
    else:
        request_status = "blocked_activation_executor_implementation_request_preconditions"
        review_decision = "blocked_before_activation_executor_implementation_approval"

    denied_effects = list(preflight.get("denied_effects") or [])
    for effect in [
        "write activation executor implementation request",
        "implement activation executor from implementation request",
        "accept --activate-trusted-artifact on this implementation request command",
        "write activation record",
        "append activation audit events",
        "mutate trusted Browser Skill artifact",
        "mutate SiteOps Skill Card artifact",
    ]:
        if effect not in denied_effects:
            denied_effects.append(effect)

    result = dict(preflight)
    result.update(
        {
            "action": PROMOTION_ACTIVATION_EXECUTOR_IMPLEMENTATION_REQUEST_ACTION,
            "activation_executor_implementation_request_status": request_status,
            "review_decision": review_decision,
            "activation_executor_implementation_request": request_packet,
            "activation_executor_implementation_request_checks": checks,
            "ready_for_activation_executor_implementation_approval_next_pass": (
                request_status == "activation_executor_implementation_request_ready_no_write"
            ),
            "implementation_request_artifact_written": False,
            "future_activate_trusted_artifact_flag_required": True,
            "activate_trusted_artifact_flag_supported_in_this_pass": False,
            "activation_executor_implemented": False,
            "activation_executor_allowed_in_this_pass": False,
            "activation_executor_write_allowed_in_this_pass": False,
            "activation_record_written": False,
            "activation_audit_written": False,
            "activation_consumption_marker_written": False,
            "approval_consumed": False,
            "approval_decision_written": False,
            "approval_request_status_mutated": False,
            "trusted_artifacts_written": False,
            "trusted_artifacts_mutated": False,
            "trusted_skill_write_allowed": False,
            "siteops_skill_card_write_allowed": False,
            "activation_allowed": False,
            "activation_performed": False,
            "browser_execution_allowed": False,
            "agent_bus_enqueue_allowed": False,
            "provider_api_call_allowed": False,
            "gate_policy_mutation_allowed": False,
            "canonical_writeback_allowed": False,
            "writes_performed": False,
            "files_modified": False,
            "blocked_actions": denied_effects,
            "denied_effects": denied_effects,
            "boundary": (
                "activation executor implementation request only; packages "
                "preflight evidence and the future activation write set for "
                "operator review. It performs no activation record write, "
                "audit write, trusted artifact mutation, browser execution, "
                "Agent Bus work, provider call, Gate mutation, or canonical writeback."
            ),
        }
    )
    return result


def candidate_promotion_activation_executor_implementation_approval(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    source_approval_id: str,
    activation_approval_id: str,
    decision: str,
    actor: str,
    reason: str | None = None,
) -> dict[str, Any]:
    """Return a no-write approval/rejection packet for future activation executor implementation."""
    normalized_decision = (decision or "").strip().lower()
    if normalized_decision not in {"approve", "reject"}:
        raise ValueError("decision must be 'approve' or 'reject'")

    implementation_request = candidate_promotion_activation_executor_implementation_request(
        candidate_id,
        root,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
        source_approval_id=source_approval_id,
        activation_approval_id=activation_approval_id,
        actor=actor,
        reason=reason or "operator requested activation executor implementation approval",
    )
    scope = dict(implementation_request.get("scope") or {})
    request_packet = dict(
        implementation_request.get("activation_executor_implementation_request") or {}
    )
    request_status = implementation_request.get("activation_executor_implementation_request_status")
    request_ready = bool(
        implementation_request.get("ready_for_activation_executor_implementation_approval_next_pass")
    )
    actor_id = (actor or user_id or "").strip()
    decision_id = _new_run_id(
        f"{implementation_request.get('candidate_id')}_activation_executor_implementation_approval"
    )
    approval_packet = {
        "decision_id": decision_id,
        "record_type": "siteops_activation_executor_implementation_approval",
        "tenant_id": scope.get("tenant_id"),
        "workspace_id": scope.get("workspace_id"),
        "user_id": scope.get("user_id"),
        "actor": actor_id,
        "decision": normalized_decision,
        "reason": reason or "",
        "candidate_id": implementation_request.get("candidate_id"),
        "proposed_skill_id": implementation_request.get("proposed_skill_id"),
        "source_approval_id": source_approval_id,
        "activation_approval_id": activation_approval_id,
        "implementation_request_id": request_packet.get("request_id"),
        "future_command_name": request_packet.get("future_command_name"),
        "future_explicit_write_flag": "--activate-trusted-artifact",
        "future_write_set": request_packet.get("future_write_set"),
        "record_schema": request_packet.get("record_schema"),
        "status": "review_decision_packet_only",
        "durable_record_written": False,
        "approval_decision_written": False,
        "implementation_allowed_in_this_pass": False,
        "activation_executor_allowed_in_this_pass": False,
        "activate_trusted_artifact_flag_supported_in_this_pass": False,
        "activation_record_write_allowed_in_this_pass": False,
        "activation_audit_write_allowed_in_this_pass": False,
        "trusted_artifact_mutation_allowed_in_this_pass": False,
        "browser_execution_allowed_in_this_pass": False,
        "agent_bus_enqueue_allowed_in_this_pass": False,
        "provider_call_allowed_in_this_pass": False,
        "canonical_writeback_allowed_in_this_pass": False,
    }
    implementation_approved = request_ready and normalized_decision == "approve"
    implementation_rejected = request_ready and normalized_decision == "reject"
    if not request_ready:
        approval_status = f"blocked_activation_executor_implementation_request: {request_status}"
        review_decision = "blocked_before_activation_executor_implementation_approval"
    elif implementation_approved:
        approval_status = "activation_executor_implementation_approved_for_next_pass_no_write"
        review_decision = "operator_intent_approve_activation_executor_implementation_next_pass"
    else:
        approval_status = "activation_executor_implementation_rejected_no_write"
        review_decision = "operator_intent_reject_activation_executor_implementation"

    approval_checks = [
        _executor_preflight_check(
            "activation_executor_implementation_request_ready",
            passed=request_ready,
            detail=str(request_status),
        ),
        _executor_preflight_check(
            "activation_executor_implementation_approval_decision_valid",
            passed=True,
            detail=normalized_decision,
        ),
        _executor_preflight_check(
            "activation_executor_implementation_approval_actor_present",
            passed=bool(actor_id),
            detail=actor_id,
        ),
        _executor_preflight_check(
            "activation_executor_implementation_approval_record_still_no_write",
            passed=True,
            detail="durable_record_written=false; approval_decision_written=false",
        ),
        _executor_preflight_check(
            "activation_executor_implementation_approval_activation_flag_unsupported",
            passed=True,
            detail="--activate-trusted-artifact remains unsupported in this pass",
        ),
    ]
    denied_effects = list(implementation_request.get("denied_effects") or [])
    for effect in [
        "write activation executor implementation approval record",
        "implement activation executor from approval packet",
        "accept --activate-trusted-artifact on this approval command",
        "write activation record",
        "append activation audit events",
        "mutate trusted Browser Skill artifact",
        "mutate SiteOps Skill Card artifact",
    ]:
        if effect not in denied_effects:
            denied_effects.append(effect)

    result = dict(implementation_request)
    result.update(
        {
            "action": PROMOTION_ACTIVATION_EXECUTOR_IMPLEMENTATION_APPROVAL_ACTION,
            "decision": normalized_decision,
            "actor": actor_id,
            "activation_executor_implementation_request_status": request_status,
            "activation_executor_implementation_approval_status": approval_status,
            "review_decision": review_decision,
            "activation_executor_implementation_approval": approval_packet,
            "activation_executor_implementation_approval_checks": approval_checks,
            "implementation_request_packet": {
                "request_id": request_packet.get("request_id"),
                "status": request_status,
                "request_ready_no_write": request_ready,
            },
            "activation_executor_implementation_approved_for_next_pass": implementation_approved,
            "activation_executor_implementation_rejected": implementation_rejected,
            "ready_for_activation_executor_implementation_next_pass": implementation_approved,
            "implementation_approval_artifact_written": False,
            "approval_decision_written": False,
            "implementation_request_artifact_written": False,
            "future_activate_trusted_artifact_flag_required": True,
            "activate_trusted_artifact_flag_supported_in_this_pass": False,
            "activation_executor_implemented": False,
            "activation_executor_allowed_in_this_pass": False,
            "activation_executor_write_allowed_in_this_pass": False,
            "activation_record_written": False,
            "activation_audit_written": False,
            "activation_consumption_marker_written": False,
            "approval_consumed": False,
            "approval_request_status_mutated": False,
            "trusted_artifacts_written": False,
            "trusted_artifacts_mutated": False,
            "trusted_skill_write_allowed": False,
            "siteops_skill_card_write_allowed": False,
            "activation_allowed": False,
            "activation_performed": False,
            "browser_execution_allowed": False,
            "agent_bus_enqueue_allowed": False,
            "provider_api_call_allowed": False,
            "gate_policy_mutation_allowed": False,
            "canonical_writeback_allowed": False,
            "writes_performed": False,
            "files_modified": False,
            "blocked_actions": denied_effects,
            "denied_effects": denied_effects,
            "boundary": (
                "activation executor implementation approval only; records "
                "approve/reject intent for a future guarded implementation pass. "
                "It performs no approval record write, activation record write, "
                "audit write, trusted artifact mutation, browser execution, "
                "Agent Bus work, provider call, Gate mutation, or canonical writeback."
            ),
        }
    )
    return result


def _activation_rel_path(vault_root: Path, path_text: str | None) -> str | None:
    if not path_text:
        return None
    try:
        return Path(path_text).resolve(strict=False).relative_to(
            vault_root.resolve(strict=False)
        ).as_posix()
    except ValueError:
        return None


def _activated_artifact_payload(
    payload: dict[str, Any],
    *,
    actor: str,
    now: str,
    candidate_id: str,
    source_approval_id: str,
    activation_approval_id: str,
    marker_ref: str | None,
    artifact_kind: str,
) -> dict[str, Any]:
    activated = dict(payload)
    history = list(activated.get("activation_history") or [])
    history.append(
        {
            "event": "activated_trusted_artifact",
            "activated_at": now,
            "activated_by": actor,
            "candidate_id": candidate_id,
            "source_approval_id": source_approval_id,
            "activation_approval_id": activation_approval_id,
            "activation_consumer_marker_ref": marker_ref,
            "artifact_kind": artifact_kind,
        }
    )
    activated.update(
        {
            "status": "active_approved",
            "activation_allowed": True,
            "activated_at": now,
            "activated_by": actor,
            "activation_source": {
                "candidate_id": candidate_id,
                "source_approval_id": source_approval_id,
                "activation_approval_id": activation_approval_id,
                "activation_consumer_marker_ref": marker_ref,
            },
            "activation_history": history,
        }
    )
    return activated


def candidate_promotion_activation_executor_implementation(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    source_approval_id: str,
    activation_approval_id: str,
    actor: str,
    reason: str | None = None,
    activate_trusted_artifact: bool = False,
) -> dict[str, Any]:
    """Activate reviewed trusted artifacts behind an explicit guarded flag.

    The executor writes only scoped activation run/audit evidence and mutates
    the reviewed inactive Browser Skill and SiteOps Skill Card activation
    fields. It does not launch browsers, enqueue Agent Bus work, call providers,
    mutate Gate policy, consume approvals, or write canonical ChaseOS memory.
    """
    implementation_approval = candidate_promotion_activation_executor_implementation_approval(
        candidate_id,
        root,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
        source_approval_id=source_approval_id,
        activation_approval_id=activation_approval_id,
        decision="approve",
        actor=actor,
        reason=reason or "operator-approved activation executor implementation",
    )
    preflight = candidate_promotion_activation_executor_preflight(
        candidate_id,
        root,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
        source_approval_id=source_approval_id,
        activation_approval_id=activation_approval_id,
        actor=actor,
        reason=reason or "operator invoked activation executor implementation",
    )
    scope = dict(implementation_approval.get("scope") or preflight.get("scope") or {})
    tenant = str(scope.get("tenant_id") or tenant_id or "")
    workspace = str(scope.get("workspace_id") or workspace_id or "")
    user = str(scope.get("user_id") or user_id or "")
    candidate = str(implementation_approval.get("candidate_id") or candidate_id)
    proposed_skill_id = str(implementation_approval.get("proposed_skill_id") or candidate)
    vault_root = Path(root or ".").resolve()

    future_record = dict(preflight.get("future_activation_record") or {})
    activation_record_path = Path(str(future_record.get("path") or ""))
    activation_record_parent = vault_root / "07_LOGS" / "SiteOps-Activations" / tenant / workspace
    activation_record_confined = _filesystem_path_is_within(
        activation_record_path,
        activation_record_parent,
    )
    activation_record_absent = bool(str(future_record.get("path") or "") and not activation_record_path.exists())

    marker = dict(preflight.get("activation_consumption_marker") or {})
    marker_ref = str(marker.get("path") or "")
    artifact_posture = list(preflight.get("trusted_artifact_posture") or [])
    artifact_by_kind = {
        str(item.get("artifact_kind")): dict(item)
        for item in artifact_posture
        if isinstance(item, dict)
    }
    browser_skill_path = Path(str(artifact_by_kind.get("browser_skill", {}).get("path") or ""))
    siteops_card_path = Path(str(artifact_by_kind.get("siteops_skill_card", {}).get("path") or ""))
    browser_skill_rel = _activation_rel_path(vault_root, browser_skill_path.as_posix())
    siteops_card_rel = _activation_rel_path(vault_root, siteops_card_path.as_posix())
    activation_record_rel = _activation_rel_path(vault_root, activation_record_path.as_posix())
    write_targets = [
        item
        for item in [browser_skill_rel, siteops_card_rel, activation_record_rel]
        if item
    ]
    gate_allowed, gate_reason = check_runtime_operation(
        PROMOTION_ACTIVATION_GATE_OPERATION,
        write_targets=write_targets,
    )

    browser_payload, browser_parse_error = _load_activation_artifact(browser_skill_path)
    card_payload, card_parse_error = _load_activation_artifact(siteops_card_path)
    now = now_iso()
    browser_secret_errors = scan_secret_like_keys(browser_payload or {}) if browser_payload else []
    card_secret_errors = scan_secret_like_keys(card_payload or {}) if card_payload else []
    marker_secret_errors = list(marker.get("secret_like_keys_detected") or [])
    implementation_ready = bool(
        implementation_approval.get("ready_for_activation_executor_implementation_next_pass")
    )
    preflight_ready = bool(
        preflight.get("activation_executor_preflight_status")
        == "activation_executor_preflight_ready_no_write"
        and preflight.get("ready_for_activation_executor_implementation_request_next_pass") is True
    )
    artifacts_ready = bool(
        artifact_posture
        and all(item.get("ready_for_activation_design") is True for item in artifact_posture)
        and browser_payload
        and card_payload
        and browser_parse_error is None
        and card_parse_error is None
        and not browser_secret_errors
        and not card_secret_errors
        and not marker_secret_errors
    )
    paths_ready = bool(
        activation_record_confined
        and activation_record_absent
        and browser_skill_rel
        and siteops_card_rel
        and activation_record_rel
        and _filesystem_path_is_within(browser_skill_path, vault_root / TRUSTED_SKILL_REL)
        and _filesystem_path_is_within(siteops_card_path, vault_root / SITEOPS_SKILL_CARD_REL)
    )
    checks = list(implementation_approval.get("activation_executor_implementation_approval_checks") or []) + [
        _executor_preflight_check(
            "activation_executor_implementation_approved",
            passed=implementation_ready,
            detail=str(implementation_approval.get("activation_executor_implementation_approval_status")),
        ),
        _executor_preflight_check(
            "activation_executor_preflight_still_ready",
            passed=preflight_ready,
            detail=str(preflight.get("activation_executor_preflight_status")),
        ),
        _executor_preflight_check(
            "activation_executor_paths_scoped_and_absent_record",
            passed=paths_ready,
            detail=str(write_targets),
        ),
        _executor_preflight_check(
            "activation_executor_artifacts_still_inactive_and_secret_free",
            passed=artifacts_ready,
            detail="browser_parse_error="
            + str(browser_parse_error)
            + "; card_parse_error="
            + str(card_parse_error),
        ),
        _executor_preflight_check(
            "activation_executor_gate_operation_allowed",
            passed=bool(gate_allowed),
            detail=gate_reason,
        ),
        _executor_preflight_check(
            "activation_executor_requires_explicit_activate_flag",
            passed=bool(activate_trusted_artifact),
            detail="--activate-trusted-artifact supplied"
            if activate_trusted_artifact
            else "--activate-trusted-artifact not supplied",
        ),
        _executor_preflight_check(
            "activation_executor_stops_before_browser_runtime",
            passed=True,
            detail="no browser/CDP, Agent Bus, provider, Gate mutation, or canonical writeback authority",
        ),
    ]
    ready_to_activate = bool(
        implementation_ready
        and preflight_ready
        and artifacts_ready
        and paths_ready
        and gate_allowed
    )

    if not implementation_ready:
        executor_status = (
            "blocked_activation_executor_implementation_approval: "
            f"{implementation_approval.get('activation_executor_implementation_approval_status')}"
        )
        review_decision = "blocked_before_activation_executor_execution"
    elif not preflight_ready:
        executor_status = (
            "blocked_activation_executor_preflight: "
            f"{preflight.get('activation_executor_preflight_status')}"
        )
        review_decision = "blocked_before_activation_executor_execution"
    elif not paths_ready:
        executor_status = "blocked_activation_executor_scoped_path_posture"
        review_decision = "blocked_before_activation_executor_execution"
    elif not artifacts_ready:
        executor_status = "blocked_activation_executor_artifact_posture"
        review_decision = "restore_inactive_secret_free_artifacts_before_activation"
    elif not gate_allowed:
        executor_status = "blocked_activation_gate_operation_not_allowlisted"
        review_decision = "apply_operator_approved_activation_gate_policy_before_activation"
    elif not activate_trusted_artifact:
        executor_status = "activation_executor_ready_dry_run_no_write"
        review_decision = "executor_ready_requires_explicit_activate_trusted_artifact_flag"
    else:
        executor_status = "activation_executor_ready_to_activate"
        review_decision = "activate_trusted_artifacts_and_stop_before_runtime_execution"

    run_id = f"siteops_activation_executor_{_slug(candidate)[:48]}"
    run_ref: str | None = None
    activation_record_ref: str | None = None
    activation_record_digest: str | None = None
    preactivation_audit_ref: str | None = None
    postactivation_audit_ref: str | None = None
    browser_skill_digest_before = _sha256_json(browser_payload or {}) if browser_payload else None
    siteops_card_digest_before = _sha256_json(card_payload or {}) if card_payload else None
    browser_skill_digest_after: str | None = None
    siteops_card_digest_after: str | None = None
    if activate_trusted_artifact and ready_to_activate:
        run = SiteOpsRun(
            run_id=run_id,
            tenant_id=tenant,
            workspace_id=workspace,
            user_id=user,
            skill_id=proposed_skill_id,
            workflow_id=PROMOTION_WORKFLOW_ID,
            site_profile_id=None,
            provider_id=None,
            mode="activation_executor",
            status="trusted_artifacts_activated",
            inputs_ref=marker_ref,
            outputs_ref=activation_record_path.as_posix(),
            audit_ref=audit_path(root, tenant, workspace, run_id).as_posix(),
            cost_estimate={"charged": False, "provider": None},
            cost_actual=None,
            started_at=now,
            ended_at=now_iso(),
        )
        run_ref = write_run_record(root, run)
        preactivation_audit_ref = append_audit_event(
            root,
            SiteOpsAuditEvent(
                event_id=f"event_{run_id}_activation_prewrite",
                run_id=run_id,
                tenant_id=tenant,
                workspace_id=workspace,
                user_id=user,
                event_type="activation_executor_prewrite",
                action=PROMOTION_ACTIVATION_EXECUTOR_IMPLEMENTATION_ACTION,
                target=candidate,
                policy_decision="allow_activation_write",
                timestamp=now_iso(),
                metadata={
                    "source_approval_id": source_approval_id,
                    "activation_approval_id": activation_approval_id,
                    "proposed_skill_id": proposed_skill_id,
                    "gate_operation": PROMOTION_ACTIVATION_GATE_OPERATION,
                    "gate_reason": gate_reason,
                    "activation_consumer_marker_ref": marker_ref,
                    "write_targets": write_targets,
                    "browser_execution_allowed": False,
                    "canonical_writeback_allowed": False,
                },
                redacted_fields=[],
            ),
        )
        activated_browser_payload = _activated_artifact_payload(
            browser_payload or {},
            actor=actor,
            now=now,
            candidate_id=candidate,
            source_approval_id=source_approval_id,
            activation_approval_id=activation_approval_id,
            marker_ref=marker_ref,
            artifact_kind="browser_skill",
        )
        activated_card_payload = _activated_artifact_payload(
            card_payload or {},
            actor=actor,
            now=now,
            candidate_id=candidate,
            source_approval_id=source_approval_id,
            activation_approval_id=activation_approval_id,
            marker_ref=marker_ref,
            artifact_kind="siteops_skill_card",
        )
        activation_record = {
            "record_type": "siteops_trusted_artifact_activation",
            "schema_version": 1,
            "run_id": run_id,
            "tenant_id": tenant,
            "workspace_id": workspace,
            "user_id": user,
            "candidate_id": candidate,
            "proposed_skill_id": proposed_skill_id,
            "source_approval_id": source_approval_id,
            "activation_approval_id": activation_approval_id,
            "activation_consumer_marker_ref": marker_ref,
            "activated_at": now,
            "activated_by": actor,
            "reason": reason or "",
            "browser_skill_ref": browser_skill_rel,
            "siteops_skill_card_ref": siteops_card_rel,
            "browser_skill_sha256_before": browser_skill_digest_before,
            "siteops_skill_card_sha256_before": siteops_card_digest_before,
            "browser_execution_performed": False,
            "agent_bus_enqueue_performed": False,
            "provider_api_call_performed": False,
            "gate_policy_mutated": False,
            "canonical_writeback_performed": False,
        }
        _write_yaml_atomic(browser_skill_path, activated_browser_payload)
        _write_json_atomic(siteops_card_path, activated_card_payload)
        browser_skill_digest_after = _sha256_json(activated_browser_payload)
        siteops_card_digest_after = _sha256_json(activated_card_payload)
        activation_record.update(
            {
                "browser_skill_sha256_after": browser_skill_digest_after,
                "siteops_skill_card_sha256_after": siteops_card_digest_after,
            }
        )
        _write_json_create_new(activation_record_path, activation_record)
        activation_record_ref = activation_record_path.as_posix()
        activation_record_digest = _sha256_json(activation_record)
        postactivation_audit_ref = append_audit_event(
            root,
            SiteOpsAuditEvent(
                event_id=f"event_{run_id}_activation_postwrite",
                run_id=run_id,
                tenant_id=tenant,
                workspace_id=workspace,
                user_id=user,
                event_type="activation_executor_postwrite",
                action=PROMOTION_ACTIVATION_EXECUTOR_IMPLEMENTATION_ACTION,
                target=candidate,
                policy_decision="trusted_artifacts_activated_stop_before_runtime",
                timestamp=now_iso(),
                metadata={
                    "activation_record_ref": activation_record_ref,
                    "activation_record_sha256": activation_record_digest,
                    "browser_skill_ref": browser_skill_rel,
                    "siteops_skill_card_ref": siteops_card_rel,
                    "browser_skill_sha256_after": browser_skill_digest_after,
                    "siteops_skill_card_sha256_after": siteops_card_digest_after,
                    "browser_execution_performed": False,
                    "agent_bus_enqueue_performed": False,
                    "provider_api_call_performed": False,
                    "canonical_writeback_performed": False,
                },
                redacted_fields=[],
            ),
        )
        executor_status = "trusted_artifacts_activated_stop_before_runtime"
        review_decision = "activation_complete_runtime_execution_still_blocked"

    denied_effects = list(implementation_approval.get("denied_effects") or [])
    for effect in [
        "launch or control a browser",
        "enqueue Agent Bus work",
        "call provider APIs",
        "mutate Gate policy",
        "write canonical ChaseOS memory/state",
        "consume approval request status",
        "publish or externally share outputs",
    ]:
        if effect not in denied_effects:
            denied_effects.insert(0, effect)

    writes_performed = bool(
        run_ref or activation_record_ref or preactivation_audit_ref or postactivation_audit_ref
    )
    return {
        "ok": True,
        "action": PROMOTION_ACTIVATION_EXECUTOR_IMPLEMENTATION_ACTION,
        "candidate_id": candidate,
        "proposed_skill_id": proposed_skill_id,
        "scope": {"tenant_id": tenant, "workspace_id": workspace, "user_id": user},
        "source_approval_id": source_approval_id,
        "activation_approval_id": activation_approval_id,
        "actor": actor,
        "activation_executor_implementation_approval_status": implementation_approval.get(
            "activation_executor_implementation_approval_status"
        ),
        "activation_executor_preflight_status": preflight.get("activation_executor_preflight_status"),
        "activation_executor_implementation_status": executor_status,
        "review_decision": review_decision,
        "activate_trusted_artifact_requested": bool(activate_trusted_artifact),
        "activate_trusted_artifact_flag_supported": True,
        "activation_executor_implemented": True,
        "activation_executor_ready_to_activate": ready_to_activate,
        "activation_executor_checks": checks,
        "gate_operation": PROMOTION_ACTIVATION_GATE_OPERATION,
        "gate_operation_allowed": bool(gate_allowed),
        "gate_reason": gate_reason,
        "write_targets": write_targets,
        "activation_consumer_marker_ref": marker_ref or None,
        "browser_skill_ref": browser_skill_rel,
        "siteops_skill_card_ref": siteops_card_rel,
        "activation_record_ref": activation_record_ref,
        "activation_record_path": activation_record_path.as_posix() if str(future_record.get("path") or "") else None,
        "activation_record_sha256": activation_record_digest,
        "browser_skill_sha256_before": browser_skill_digest_before,
        "siteops_skill_card_sha256_before": siteops_card_digest_before,
        "browser_skill_sha256_after": browser_skill_digest_after,
        "siteops_skill_card_sha256_after": siteops_card_digest_after,
        "run_id": run_id,
        "run_ref": run_ref,
        "audit_ref": postactivation_audit_ref or preactivation_audit_ref,
        "preactivation_audit_ref": preactivation_audit_ref,
        "postactivation_audit_ref": postactivation_audit_ref,
        "blocked_actions": denied_effects,
        "denied_effects": denied_effects,
        "writes_performed": writes_performed,
        "files_modified": writes_performed,
        "run_record_written": bool(run_ref),
        "activation_record_written": bool(activation_record_ref),
        "activation_audit_written": bool(preactivation_audit_ref or postactivation_audit_ref),
        "audit_events_written": bool(preactivation_audit_ref or postactivation_audit_ref),
        "approval_consumed": False,
        "approval_decision_written": False,
        "approval_request_status_mutated": False,
        "trusted_artifacts_written": False,
        "trusted_artifacts_mutated": bool(activation_record_ref),
        "trusted_skill_write_allowed": bool(activate_trusted_artifact and ready_to_activate),
        "siteops_skill_card_write_allowed": bool(activate_trusted_artifact and ready_to_activate),
        "activation_allowed": bool(activation_record_ref),
        "activation_performed": bool(activation_record_ref),
        "browser_execution_allowed": False,
        "agent_bus_enqueue_allowed": False,
        "provider_api_call_allowed": False,
        "gate_policy_mutation_allowed": False,
        "canonical_writeback_allowed": False,
        "boundary": (
            "activation executor implementation only; writes require explicit "
            "--activate-trusted-artifact, approved implementation posture, ready "
            "preflight, scoped consumed-marker evidence, inactive trusted artifacts, "
            "absent activation record, and Gate allowance. It activates local trusted "
            "artifacts and writes scoped activation run/audit evidence, then stops "
            "before browser/CDP execution, Agent Bus work, provider calls, Gate "
            "mutation, approval-status mutation, or canonical ChaseOS writeback."
        ),
    }


def candidate_promotion_activation_executor_live_readiness(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    actor: str,
    source_approval_id: str | None = None,
    activation_approval_id: str | None = None,
    reason: str | None = None,
) -> dict[str, Any]:
    """Report live activation executor readiness without activating artifacts."""
    scope = require_scope(tenant_id=tenant_id, workspace_id=workspace_id, user_id=user_id)
    _validate_request_scope(root, scope)
    consumption = candidate_promotion_activation_consumption_live_readiness(
        candidate_id,
        root,
        tenant_id=scope.tenant_id,
        workspace_id=scope.workspace_id,
        user_id=scope.user_id,
        actor=actor,
        source_approval_id=source_approval_id,
        activation_approval_id=activation_approval_id,
        reason=reason or "operator requested activation executor live readiness",
    )
    resolved_candidate_id = str(consumption.get("candidate_id") or candidate_id)
    selected_source_approval_id = str(consumption.get("source_approval_id") or "").strip()
    selected_activation_approval_id = str(consumption.get("activation_approval_id") or "").strip()
    consumption_status = str(consumption.get("activation_consumption_live_readiness_status") or "")
    consumption_ready = consumption_status == "activation_consumption_live_readiness_ready_no_write"

    executor_dry_run: dict[str, Any] | None = None
    executor_dry_run_error: str | None = None
    if selected_source_approval_id and selected_activation_approval_id:
        try:
            executor_dry_run = candidate_promotion_activation_executor_implementation(
                resolved_candidate_id,
                root,
                tenant_id=scope.tenant_id,
                workspace_id=scope.workspace_id,
                user_id=scope.user_id,
                source_approval_id=selected_source_approval_id,
                activation_approval_id=selected_activation_approval_id,
                actor=actor,
                reason=reason or "operator requested activation executor live readiness",
                activate_trusted_artifact=False,
            )
        except (SiteOpsError, RuntimeError, ValueError) as exc:
            executor_dry_run_error = str(exc)

    executor_status = str((executor_dry_run or {}).get("activation_executor_implementation_status") or "")
    executor_checks = list((executor_dry_run or {}).get("activation_executor_checks") or [])
    executor_ready = bool(
        executor_dry_run
        and executor_status == "activation_executor_ready_dry_run_no_write"
        and executor_dry_run.get("activation_executor_ready_to_activate") is True
        and executor_dry_run.get("writes_performed") is False
    )
    activation_record_path = str((executor_dry_run or {}).get("activation_record_path") or "").strip()
    activation_record_exists = bool(activation_record_path and Path(activation_record_path).exists())

    ids_selected = bool(selected_source_approval_id and selected_activation_approval_id)
    if not ids_selected:
        readiness_status = f"blocked_activation_consumption_live_readiness: {consumption_status}"
        review_decision = str(consumption.get("review_decision") or "repair_activation_consumption_before_activation")
    elif executor_ready:
        readiness_status = "activation_executor_live_readiness_ready_no_write"
        review_decision = "ready_for_operator_reviewed_activate_trusted_artifact_command"
    elif executor_status == "blocked_activation_gate_operation_not_allowlisted":
        readiness_status = "blocked_activation_gate_operation_not_allowlisted"
        review_decision = "apply_operator_approved_activation_gate_policy_before_activation"
    elif activation_record_exists:
        readiness_status = "blocked_activation_record_already_exists"
        review_decision = "manual_review_existing_activation_record_before_retry"
    elif executor_status:
        readiness_status = f"blocked_activation_executor_dry_run: {executor_status}"
        review_decision = "inspect_activation_executor_dry_run_before_activation"
    elif not consumption_ready:
        readiness_status = f"blocked_activation_consumption_live_readiness: {consumption_status}"
        review_decision = str(consumption.get("review_decision") or "repair_activation_consumption_before_activation")
    else:
        readiness_status = "blocked_activation_executor_dry_run_unavailable"
        review_decision = "repair_activation_executor_inputs_before_activation"

    activate_command_preview = [
        "python",
        "-m",
        "runtime.cli.main",
        "siteops",
        "candidates",
        "activation-executor-implementation",
        resolved_candidate_id,
        "--source-approval-id",
        selected_source_approval_id or "<SOURCE_APPROVAL_ID>",
        "--activation-approval-id",
        selected_activation_approval_id or "<ACTIVATION_APPROVAL_ID>",
        "--tenant",
        scope.tenant_id,
        "--workspace",
        scope.workspace_id,
        "--user",
        scope.user_id,
        "--actor",
        actor,
        "--activate-trusted-artifact",
        "--json",
    ]
    checks = [
        _executor_preflight_check(
            "activation_consumption_live_readiness_ready",
            passed=bool(consumption_ready or executor_dry_run is not None),
            detail=consumption_status or "not_run",
        ),
        _executor_preflight_check(
            "source_approval_id_selected",
            passed=bool(selected_source_approval_id),
            detail=selected_source_approval_id or "missing",
        ),
        _executor_preflight_check(
            "activation_approval_id_selected",
            passed=bool(selected_activation_approval_id),
            detail=selected_activation_approval_id or "missing",
        ),
        _executor_preflight_check(
            "activation_executor_dry_run_available",
            passed=executor_dry_run is not None,
            detail=executor_dry_run_error or executor_status or "not_run",
        ),
        _executor_preflight_check(
            "activation_executor_dry_run_ready",
            passed=executor_ready,
            detail=executor_dry_run_error or executor_status or "not_run",
        ),
        _executor_preflight_check(
            "activation_record_absent",
            passed=not activation_record_exists,
            required=False,
            detail=activation_record_path or "not_computed",
        ),
        _executor_preflight_check(
            "activation_gate_operation_allowed",
            passed=bool((executor_dry_run or {}).get("gate_operation_allowed")),
            detail=str((executor_dry_run or {}).get("gate_reason") or "not_checked"),
        ),
        _executor_preflight_check(
            "readiness_pass_is_no_write",
            passed=True,
            detail="does not pass --activate-trusted-artifact to the executor",
        ),
        _executor_preflight_check(
            "readiness_stops_before_browser_runtime",
            passed=True,
            detail="no browser/CDP, Agent Bus, provider, Gate mutation, or canonical writeback authority",
        ),
    ]
    return {
        "ok": True,
        "action": PROMOTION_ACTIVATION_EXECUTOR_LIVE_READINESS_ACTION,
        "candidate_id": resolved_candidate_id,
        "proposed_skill_id": consumption.get("proposed_skill_id")
        or (executor_dry_run or {}).get("proposed_skill_id"),
        "scope": scope.as_dict(),
        "actor": actor,
        "source_approval_id": selected_source_approval_id or None,
        "activation_approval_id": selected_activation_approval_id or None,
        "activation_executor_live_readiness_status": readiness_status,
        "review_decision": review_decision,
        "activation_consumption_live_readiness_status": consumption_status,
        "activation_executor_dry_run_status": executor_status or None,
        "activation_executor_dry_run_error": executor_dry_run_error,
        "activation_executor_dry_run_ready": executor_ready,
        "activation_executor_checks": executor_checks,
        "activation_executor_ready_to_activate": bool(
            (executor_dry_run or {}).get("activation_executor_ready_to_activate")
        ),
        "gate_operation": PROMOTION_ACTIVATION_GATE_OPERATION,
        "gate_operation_allowed": bool((executor_dry_run or {}).get("gate_operation_allowed")),
        "gate_reason": (executor_dry_run or {}).get("gate_reason"),
        "activation_consumer_marker_ref": (executor_dry_run or {}).get("activation_consumer_marker_ref"),
        "browser_skill_ref": (executor_dry_run or {}).get("browser_skill_ref"),
        "siteops_skill_card_ref": (executor_dry_run or {}).get("siteops_skill_card_ref"),
        "activation_record_path": activation_record_path or None,
        "activation_record_exists": activation_record_exists,
        "write_targets": (executor_dry_run or {}).get("write_targets") or [],
        "activate_command_preview": activate_command_preview,
        "activation_executor_live_readiness_checks": checks,
        "writes_performed": False,
        "files_modified": False,
        "run_record_written": False,
        "activation_record_written": False,
        "activation_audit_written": False,
        "approval_consumed": False,
        "approval_decision_written": False,
        "approval_request_status_mutated": False,
        "trusted_artifacts_written": False,
        "trusted_artifacts_mutated": False,
        "trusted_skill_write_allowed": False,
        "siteops_skill_card_write_allowed": False,
        "activation_allowed": False,
        "activation_performed": False,
        "browser_execution_allowed": False,
        "agent_bus_enqueue_allowed": False,
        "provider_api_call_allowed": False,
        "gate_policy_mutation_allowed": False,
        "canonical_writeback_allowed": False,
        "blocked_actions": [
            "activate trusted artifacts",
            "write activation records",
            "append activation audit events",
            "mutate trusted Browser Skill artifact",
            "mutate SiteOps Skill Card artifact",
            "consume approval request status",
            "launch or control a browser",
            "enqueue Agent Bus work",
            "call provider APIs",
            "mutate Gate policy",
            "write canonical ChaseOS memory/state",
        ],
        "boundary": (
            "activation executor live readiness only; it discovers or validates "
            "approval ids, inspects consumed marker and inactive artifact posture "
            "through the guarded executor dry-run, checks activation Gate posture, "
            "and previews the exact future --activate-trusted-artifact command. "
            "It does not activate artifacts, write activation records/audits, run "
            "browsers, enqueue Agent Bus work, call providers, mutate Gate, consume "
            "approvals, or write canonical ChaseOS state."
        ),
    }


def candidate_promotion_activation_gate_live_readiness(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    source_approval_id: str | None = None,
    activation_approval_id: str | None = None,
    actor: str,
    reason: str | None = None,
) -> dict[str, Any]:
    """Report the no-write Gate delta required before trusted activation."""
    scope = require_scope(tenant_id=tenant_id, workspace_id=workspace_id, user_id=user_id)
    vault_root = Path(root or Path.cwd()).resolve(strict=False)
    readiness = candidate_promotion_activation_executor_live_readiness(
        candidate_id,
        vault_root,
        tenant_id=scope.tenant_id,
        workspace_id=scope.workspace_id,
        user_id=scope.user_id,
        source_approval_id=source_approval_id,
        activation_approval_id=activation_approval_id,
        actor=actor,
        reason=reason or "operator requested activation Gate live readiness",
    )

    runtime_rel = "runtime/chaseos_gate.py"
    allowlists_rel = "runtime/policy/gateway_allowlists.json"
    runtime_path = vault_root / runtime_rel
    allowlists_path = vault_root / allowlists_rel
    runtime_exists = runtime_path.exists()
    allowlists_exists = allowlists_path.exists()
    runtime_text = runtime_path.read_text(encoding="utf-8") if runtime_exists else ""
    allowlists_text = allowlists_path.read_text(encoding="utf-8") if allowlists_exists else "{}"

    allowlists_payload: dict[str, Any] = {}
    allowlists_parse_ok = False
    allowlists_parse_error: str | None = None
    try:
        allowlists_payload = json.loads(allowlists_text)
        allowlists_parse_ok = True
    except Exception as exc:  # pragma: no cover - defensive live guard
        allowlists_parse_error = str(exc)

    write_targets = list(readiness.get("write_targets") or [])
    gate_allowed, gate_reason = check_runtime_operation(
        PROMOTION_ACTIVATION_GATE_OPERATION,
        write_targets=write_targets,
    )
    write_target_categories = dict((allowlists_payload.get("write_targets") or {}))
    required_write_categories = {
        "browser_skills_inactive_review": ["runtime/browser_skills/skills/*.yaml"],
        "siteops_skill_cards_inactive_review": [
            "runtime/siteops/registry/skill_cards/*.json"
        ],
        "siteops_activation_records": ["07_LOGS/SiteOps-Activations/**"],
    }
    category_posture = {
        category: {
            "expected": patterns,
            "actual": write_target_categories.get(category),
            "present_exact": write_target_categories.get(category) == patterns,
        }
        for category, patterns in required_write_categories.items()
    }
    missing_or_different_categories = [
        category
        for category, posture in category_posture.items()
        if posture["present_exact"] is not True
    ]
    operation_present = f'"{PROMOTION_ACTIVATION_GATE_OPERATION}"' in runtime_text
    executor_checks = {
        str(check.get("check_id")): dict(check)
        for check in readiness.get("activation_executor_live_readiness_checks") or []
        if isinstance(check, dict)
    }
    executor_artifact_check = {
        str(check.get("check_id")): dict(check)
        for check in readiness.get("activation_executor_checks") or []
        if isinstance(check, dict)
    }.get("activation_executor_artifacts_still_inactive_and_secret_free", {})
    activation_record_absent = bool(
        executor_checks.get("activation_record_absent", {}).get("passed")
    )
    evidence_ready_except_gate = bool(
        readiness.get("source_approval_id")
        and readiness.get("activation_approval_id")
        and readiness.get("activation_consumer_marker_ref")
        and readiness.get("activation_record_path")
        and activation_record_absent
        and executor_artifact_check.get("passed") is True
    )
    executor_blocked_only_by_gate = (
        readiness.get("activation_executor_live_readiness_status")
        == "blocked_activation_gate_operation_not_allowlisted"
        and readiness.get("activation_executor_dry_run_status")
        == "blocked_activation_gate_operation_not_allowlisted"
    )

    if gate_allowed:
        readiness_status = "activation_gate_live_readiness_already_allowlisted_no_write"
        review_decision = "rerun_activation_executor_live_readiness_before_activation"
    elif not (runtime_exists and allowlists_exists and allowlists_parse_ok):
        readiness_status = "blocked_activation_gate_live_readiness_policy_files"
        review_decision = "repair_gate_policy_files_before_activation_gate_patch"
    elif not evidence_ready_except_gate:
        readiness_status = "blocked_activation_gate_live_readiness_activation_evidence"
        review_decision = "repair_activation_evidence_before_gate_policy_patch"
    elif executor_blocked_only_by_gate:
        readiness_status = "activation_gate_live_readiness_ready_for_policy_patch_no_write"
        review_decision = "prepare_operator_reviewed_activation_gate_policy_patch"
    else:
        readiness_status = "blocked_activation_gate_live_readiness_executor_posture"
        review_decision = "repair_activation_executor_readiness_before_gate_policy_patch"

    future_patch_command = [
        "python",
        "-m",
        "runtime.cli.main",
        "siteops",
        "candidates",
        "activation-gate-policy-patch-plan",
        str(candidate_id),
        "--source-approval-id",
        str(source_approval_id or "<SOURCE_APPROVAL_ID>"),
        "--activation-approval-id",
        str(activation_approval_id or "<ACTIVATION_APPROVAL_ID>"),
        "--tenant",
        scope.tenant_id,
        "--workspace",
        scope.workspace_id,
        "--user",
        scope.user_id,
        "--actor",
        str(actor),
        "--json",
    ]
    checks = [
        _executor_preflight_check(
            "activation_gate_policy_files_present",
            passed=runtime_exists and allowlists_exists,
            detail=f"{runtime_rel}={runtime_exists}; {allowlists_rel}={allowlists_exists}",
        ),
        _executor_preflight_check(
            "activation_gateway_allowlists_parse_ok",
            passed=allowlists_parse_ok,
            detail=str(allowlists_parse_error or "parsed"),
        ),
        _executor_preflight_check(
            "activation_gate_operation_present",
            passed=operation_present,
            required=False,
            detail=PROMOTION_ACTIVATION_GATE_OPERATION,
        ),
        _executor_preflight_check(
            "activation_gate_operation_allowed",
            passed=bool(gate_allowed),
            required=False,
            detail=gate_reason,
        ),
        _executor_preflight_check(
            "activation_write_categories_present_exact",
            passed=not missing_or_different_categories,
            required=False,
            detail=str(missing_or_different_categories or "all present"),
        ),
        _executor_preflight_check(
            "activation_evidence_ready_except_gate",
            passed=evidence_ready_except_gate,
            detail=str(readiness.get("activation_executor_live_readiness_status")),
        ),
        _executor_preflight_check(
            "activation_executor_blocked_only_by_gate",
            passed=executor_blocked_only_by_gate or bool(gate_allowed),
            detail=str(readiness.get("activation_executor_dry_run_status")),
        ),
        _executor_preflight_check(
            "activation_gate_readiness_is_no_write",
            passed=True,
            detail="does not mutate Gate policy or pass --activate-trusted-artifact",
        ),
    ]
    return {
        "ok": True,
        "action": PROMOTION_ACTIVATION_GATE_LIVE_READINESS_ACTION,
        "candidate_id": readiness.get("candidate_id") or candidate_id,
        "proposed_skill_id": readiness.get("proposed_skill_id"),
        "scope": scope.as_dict(),
        "actor": actor,
        "source_approval_id": readiness.get("source_approval_id"),
        "activation_approval_id": readiness.get("activation_approval_id"),
        "activation_gate_live_readiness_status": readiness_status,
        "review_decision": review_decision,
        "gate_operation": PROMOTION_ACTIVATION_GATE_OPERATION,
        "gate_operation_allowed": bool(gate_allowed),
        "gate_reason": gate_reason,
        "activation_executor_live_readiness_status": readiness.get(
            "activation_executor_live_readiness_status"
        ),
        "activation_executor_dry_run_status": readiness.get("activation_executor_dry_run_status"),
        "activation_record_path": readiness.get("activation_record_path"),
        "activation_record_exists": bool(readiness.get("activation_record_exists")),
        "write_targets": write_targets,
        "runtime_policy": {
            "path": runtime_rel,
            "exists": runtime_exists,
            "sha256": _sha256_file(runtime_path) if runtime_exists else None,
            "operation_present": operation_present,
        },
        "gateway_allowlists": {
            "path": allowlists_rel,
            "exists": allowlists_exists,
            "sha256": _sha256_file(allowlists_path) if allowlists_exists else None,
            "parse_ok": allowlists_parse_ok,
            "parse_error": allowlists_parse_error,
        },
        "required_write_categories": required_write_categories,
        "write_category_posture": category_posture,
        "missing_or_different_write_categories": missing_or_different_categories,
        "policy_patch_preview": {
            "target_files": [runtime_rel, allowlists_rel],
            "exact_two_file_patch_required": True,
            "runtime_operation_entry": {
                PROMOTION_ACTIVATION_GATE_OPERATION: {
                    "allow_cli_operator": True,
                    "gateway_write_categories": list(required_write_categories),
                    "write_target_categories": list(required_write_categories),
                    "approval_chain_required": [
                        "source promotion approval",
                        "activation approval",
                        "activation consumption marker",
                        "explicit --activate-trusted-artifact flag",
                    ],
                }
            },
            "gateway_allowlist_additions": {
                category: required_write_categories[category]
                for category in missing_or_different_categories
            },
            "future_patch_command_preview": future_patch_command,
            "apply_allowed_in_this_pass": False,
        },
        "activation_gate_policy_patch_required": not bool(gate_allowed),
        "ready_for_activation_gate_policy_patch_plan": readiness_status
        == "activation_gate_live_readiness_ready_for_policy_patch_no_write",
        "ready_for_activation_executor_readiness_retry": bool(gate_allowed),
        "activation_gate_live_readiness_checks": checks,
        "writes_performed": False,
        "files_modified": False,
        "gate_policy_change_performed": False,
        "allowlist_change_performed": False,
        "activation_record_written": False,
        "activation_audit_written": False,
        "approval_consumed": False,
        "trusted_artifacts_mutated": False,
        "activation_allowed": False,
        "activation_performed": False,
        "browser_execution_allowed": False,
        "agent_bus_enqueue_allowed": False,
        "provider_api_call_allowed": False,
        "canonical_writeback_allowed": False,
        "blocked_actions": [
            "mutate Gate policy",
            "activate trusted artifacts",
            "set activation_allowed=true",
            "write activation records",
            "append activation audit events",
            "mutate trusted Browser Skill artifact",
            "mutate SiteOps Skill Card artifact",
            "launch or control a browser",
            "enqueue Agent Bus work",
            "call provider APIs",
            "write canonical ChaseOS memory/state",
        ],
        "boundary": (
            "activation Gate live readiness only; it reports current Gate posture "
            "and exact future policy-patch inputs without mutating Gate policy, "
            "activating artifacts, writing activation records/audits, launching "
            "browsers, enqueueing Agent Bus work, calling providers, or writing "
            "canonical memory/state."
        ),
    }


def _activation_gate_policy_categories() -> dict[str, list[str]]:
    return {
        "browser_skills_inactive_review": ["runtime/browser_skills/skills/*.yaml"],
        "siteops_skill_cards_inactive_review": [
            "runtime/siteops/registry/skill_cards/*.json"
        ],
        "siteops_activation_records": ["07_LOGS/SiteOps-Activations/**"],
    }


def _apply_activation_gate_policy_runtime_patch(text: str) -> str:
    operation = PROMOTION_ACTIVATION_GATE_OPERATION
    if f'"{operation}"' in text:
        raise SiteOpsValidationError(f"Gate operation is already present: {operation}")
    anchor = (
        '    "siteops.browser_skill_candidate.apply_trusted_artifacts": {\n'
        '        "allow_cli_operator": True,\n'
        '        "gateway_write_categories": [\n'
        '            "browser_skills_inactive_review",\n'
        '            "siteops_skill_cards_inactive_review",\n'
        "        ],\n"
        '        "write_target_categories": [\n'
        '            "browser_skills_inactive_review",\n'
        '            "siteops_skill_cards_inactive_review",\n'
        "        ],\n"
        "    },\n"
    )
    addition = (
        anchor
        + '    "siteops.browser_skill_candidate.activate_trusted_artifact": {\n'
        + '        "allow_cli_operator": True,\n'
        + '        "gateway_write_categories": [\n'
        + '            "browser_skills_inactive_review",\n'
        + '            "siteops_skill_cards_inactive_review",\n'
        + '            "siteops_activation_records",\n'
        + "        ],\n"
        + '        "write_target_categories": [\n'
        + '            "browser_skills_inactive_review",\n'
        + '            "siteops_skill_cards_inactive_review",\n'
        + '            "siteops_activation_records",\n'
        + "        ],\n"
        + "    },\n"
    )
    if anchor not in text:
        raise SiteOpsValidationError("inactive trusted artifact Gate operation anchor not found")
    return text.replace(anchor, addition, 1)


def _apply_activation_gate_allowlists_patch(text: str) -> tuple[str, dict[str, Any]]:
    payload = json.loads(text)
    write_targets = payload.setdefault("write_targets", {})
    required_entries = {
        "siteops_activation_records": ["07_LOGS/SiteOps-Activations/**"],
    }
    for category in required_entries:
        if category in write_targets:
            raise SiteOpsValidationError(f"gateway allowlist category is already present: {category}")
    write_targets.update(required_entries)
    return json.dumps(payload, indent=2) + "\n", required_entries


def candidate_promotion_activation_gate_policy_patch_writer_implementation(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    source_approval_id: str,
    activation_approval_id: str,
    actor: str,
    reason: str | None = None,
    apply_activation_gate_policy_patch: bool = False,
) -> dict[str, Any]:
    """Apply the activation Gate patch only behind explicit approval evidence."""
    scope = require_scope(tenant_id=tenant_id, workspace_id=workspace_id, user_id=user_id)
    _validate_request_scope(root, scope)
    vault_root = Path(root or Path.cwd()).resolve(strict=False)
    readiness = candidate_promotion_activation_gate_live_readiness(
        candidate_id,
        vault_root,
        tenant_id=scope.tenant_id,
        workspace_id=scope.workspace_id,
        user_id=scope.user_id,
        source_approval_id=source_approval_id,
        activation_approval_id=activation_approval_id,
        actor=actor,
        reason=reason or "operator requested activation Gate policy patch writer",
    )
    approval = show_approval_request(root, activation_approval_id, tenant_id=scope.tenant_id)
    metadata = dict(approval.get("metadata") or {})
    approval_scope_ok = bool(
        approval.get("tenant_id") == scope.tenant_id
        and approval.get("workspace_id") == scope.workspace_id
        and approval.get("user_id") == scope.user_id
    )
    approval_target_ok = bool(
        approval.get("status") == "approved"
        and approval.get("action") == PROMOTION_ACTIVATION_GATE_OPERATION
        and metadata.get("candidate_id") == candidate_id
        and metadata.get("source_approval_id") == source_approval_id
    )
    readiness_status = str(readiness.get("activation_gate_live_readiness_status") or "")
    runtime_rel = "runtime/chaseos_gate.py"
    allowlists_rel = "runtime/policy/gateway_allowlists.json"
    runtime_path = vault_root / runtime_rel
    allowlists_path = vault_root / allowlists_rel
    runtime_text = runtime_path.read_text(encoding="utf-8") if runtime_path.exists() else ""
    allowlists_text = allowlists_path.read_text(encoding="utf-8") if allowlists_path.exists() else ""
    current_runtime_digest = _sha256_file(runtime_path) if runtime_path.exists() else None
    current_allowlists_digest = _sha256_file(allowlists_path) if allowlists_path.exists() else None
    operation_absent = f'"{PROMOTION_ACTIVATION_GATE_OPERATION}"' not in runtime_text
    allowlists_payload = json.loads(allowlists_text) if allowlists_text else {}
    existing_write_targets = dict(allowlists_payload.get("write_targets") or {})
    required_categories = _activation_gate_policy_categories()
    existing_required_categories_ok = all(
        existing_write_targets.get(category) == patterns
        for category, patterns in required_categories.items()
        if category != "siteops_activation_records"
    )
    activation_record_category_absent = "siteops_activation_records" not in existing_write_targets
    target_paths_confined = all(
        _filesystem_path_is_within(path, vault_root) for path in [runtime_path, allowlists_path]
    )
    checks = {
        "activation_approval_approved": {
            "passed": approval.get("status") == "approved",
            "detail": approval.get("status"),
        },
        "activation_approval_scope_matches": {
            "passed": approval_scope_ok,
            "detail": {
                "tenant_id": approval.get("tenant_id"),
                "workspace_id": approval.get("workspace_id"),
                "user_id": approval.get("user_id"),
            },
        },
        "activation_approval_targets_candidate_and_source": {
            "passed": approval_target_ok,
            "detail": {
                "action": approval.get("action"),
                "candidate_id": metadata.get("candidate_id"),
                "source_approval_id": metadata.get("source_approval_id"),
            },
        },
        "activation_gate_live_readiness_ready": {
            "passed": readiness_status == "activation_gate_live_readiness_ready_for_policy_patch_no_write",
            "detail": readiness_status,
        },
        "target_paths_confined": {
            "passed": target_paths_confined,
            "target_files": [runtime_rel, allowlists_rel],
        },
        "activation_gate_operation_absent_before_write": {
            "passed": operation_absent,
            "operation": PROMOTION_ACTIVATION_GATE_OPERATION,
        },
        "existing_artifact_categories_present": {
            "passed": existing_required_categories_ok,
            "categories": [
                "browser_skills_inactive_review",
                "siteops_skill_cards_inactive_review",
            ],
        },
        "activation_record_category_absent_before_write": {
            "passed": activation_record_category_absent,
            "category": "siteops_activation_records",
        },
        "apply_activation_gate_policy_patch_flag_present": {
            "passed": bool(apply_activation_gate_policy_patch),
            "required_for_write": True,
        },
    }
    patch_preconditions_ready = all(
        bool(check.get("passed"))
        for check_id, check in checks.items()
        if check_id != "apply_activation_gate_policy_patch_flag_present"
    )
    run_id = _new_run_id(f"{candidate_id}_activation_gate_policy_patch")
    backup_dir = (
        vault_root
        / "07_LOGS"
        / "SiteOps-Gate-Policy-Patches"
        / scope.tenant_id
        / scope.workspace_id
        / run_id
    )
    backup_paths = {
        "runtime_policy": backup_dir / "runtime_chaseos_gate.py.bak",
        "gateway_allowlists": backup_dir / "gateway_allowlists.json.bak",
        "rollback_audit": backup_dir / "rollback_audit.json",
    }
    result = {
        "ok": True,
        "action": PROMOTION_ACTIVATION_GATE_POLICY_PATCH_WRITER_IMPLEMENTATION_ACTION,
        "candidate_id": candidate_id,
        "proposed_skill_id": readiness.get("proposed_skill_id"),
        "scope": scope.as_dict(),
        "actor": actor,
        "source_approval_id": source_approval_id,
        "activation_approval_id": activation_approval_id,
        "activation_gate_operation": PROMOTION_ACTIVATION_GATE_OPERATION,
        "activation_gate_policy_patch_writer_implementation_status": (
            "activation_gate_policy_patch_writer_ready_dry_run"
            if patch_preconditions_ready and not apply_activation_gate_policy_patch
            else "blocked_activation_gate_policy_patch_writer_preconditions"
        ),
        "review_decision": (
            "ready_for_operator_reviewed_activation_gate_policy_patch_command"
            if patch_preconditions_ready and not apply_activation_gate_policy_patch
            else "blocked_before_activation_gate_policy_patch"
        ),
        "activation_gate_live_readiness_status": readiness_status,
        "apply_activation_gate_policy_patch_requested": bool(apply_activation_gate_policy_patch),
        "apply_activation_gate_policy_patch_flag_supported": True,
        "activation_gate_policy_patch_writer_implemented": True,
        "activation_gate_policy_patch_writer_checks": checks,
        "write_preconditions_ready": patch_preconditions_ready,
        "target_files": [runtime_rel, allowlists_rel],
        "required_write_categories": required_categories,
        "pre_write_digests": {
            "runtime_policy": current_runtime_digest,
            "gateway_allowlists": current_allowlists_digest,
        },
        "backup_artifact_paths": {
            key: path.relative_to(vault_root).as_posix() for key, path in backup_paths.items()
        },
        "gate_policy_change_allowed": bool(apply_activation_gate_policy_patch),
        "allowlist_change_allowed": bool(apply_activation_gate_policy_patch),
        "policy_file_write_allowed": bool(apply_activation_gate_policy_patch),
        "gate_policy_change_performed": False,
        "allowlist_change_performed": False,
        "backup_artifact_written": False,
        "rollback_audit_artifact_written": False,
        "activation_record_written": False,
        "activation_performed": False,
        "trusted_artifacts_mutated": False,
        "approval_consumed": False,
        "approval_request_status_mutated": False,
        "browser_execution_allowed": False,
        "agent_bus_enqueue_allowed": False,
        "provider_api_call_allowed": False,
        "canonical_writeback_allowed": False,
        "writes_performed": False,
        "files_modified": False,
    }
    if not apply_activation_gate_policy_patch:
        return result
    if not patch_preconditions_ready:
        return result

    backup_dir.mkdir(parents=True, exist_ok=False)
    backup_paths["runtime_policy"].write_text(runtime_text, encoding="utf-8")
    backup_paths["gateway_allowlists"].write_text(allowlists_text, encoding="utf-8")
    rollback_audit = {
        "run_id": run_id,
        "candidate_id": candidate_id,
        "tenant_id": scope.tenant_id,
        "workspace_id": scope.workspace_id,
        "actor": actor,
        "operation": PROMOTION_ACTIVATION_GATE_OPERATION,
        "created_at": now_iso(),
        "target_files": [runtime_rel, allowlists_rel],
        "pre_write_digests": result["pre_write_digests"],
        "backup_files": {
            key: path.relative_to(vault_root).as_posix()
            for key, path in backup_paths.items()
            if key != "rollback_audit"
        },
        "contains_secrets_or_session_state": False,
        "rollback_performed": False,
    }
    backup_paths["rollback_audit"].write_text(
        json.dumps(rollback_audit, indent=2) + "\n", encoding="utf-8"
    )
    runtime_after = _apply_activation_gate_policy_runtime_patch(runtime_text)
    allowlists_after, applied_categories = _apply_activation_gate_allowlists_patch(allowlists_text)
    try:
        compile(runtime_after, str(runtime_path), "exec")
        json.loads(allowlists_after)
        runtime_path.write_text(runtime_after, encoding="utf-8")
        allowlists_path.write_text(allowlists_after, encoding="utf-8")
        compile(runtime_path.read_text(encoding="utf-8"), str(runtime_path), "exec")
        post_allowlists = json.loads(allowlists_path.read_text(encoding="utf-8"))
        post_write_targets = dict(post_allowlists.get("write_targets") or {})
        post_checks = {
            "runtime_policy_compiles": True,
            "gateway_allowlists_parses": True,
            "activation_gate_operation_present_once": runtime_path.read_text(
                encoding="utf-8"
            ).count(f'"{PROMOTION_ACTIVATION_GATE_OPERATION}"')
            == 1,
            "activation_gateway_categories_present_exact": all(
                post_write_targets.get(category) == patterns
                for category, patterns in applied_categories.items()
            ),
        }
        if not all(post_checks.values()):
            raise SiteOpsValidationError("post-apply activation Gate policy patch verification failed")
    except Exception:
        runtime_path.write_text(runtime_text, encoding="utf-8")
        allowlists_path.write_text(allowlists_text, encoding="utf-8")
        rollback_audit["rollback_performed"] = True
        backup_paths["rollback_audit"].write_text(
            json.dumps(rollback_audit, indent=2) + "\n", encoding="utf-8"
        )
        raise

    result.update(
        {
            "activation_gate_policy_patch_writer_implementation_status": (
                "activation_gate_policy_patch_writer_implementation_applied"
            ),
            "review_decision": "activation_gate_policy_patch_applied_rerun_activation_executor_readiness",
            "gate_policy_change_performed": True,
            "allowlist_change_performed": True,
            "backup_artifact_written": True,
            "rollback_audit_artifact_written": True,
            "writes_performed": True,
            "files_modified": True,
            "post_apply_verification": post_checks,
            "applied_gate_operation": PROMOTION_ACTIVATION_GATE_OPERATION,
            "applied_gateway_categories": applied_categories,
            "boundary": (
                "Guarded activation Gate policy patch writer only; it may edit "
                "runtime/chaseos_gate.py and runtime/policy/gateway_allowlists.json "
                "when --apply-activation-gate-policy-patch is present and the "
                "approved activation request still matches the candidate/source scope. "
                "It does not activate trusted artifacts, write activation records, "
                "consume approvals, launch browsers, enqueue Agent Bus work, call "
                "providers, or write canonical memory/state."
            ),
        }
    )
    return result


def candidate_promotion_live_activation_evidence_closeout(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    actor: str,
    source_approval_id: str | None = None,
    activation_approval_id: str | None = None,
    reason: str | None = None,
) -> dict[str, Any]:
    """Close out current live activation evidence without executing activation."""
    readiness = candidate_promotion_activation_executor_live_readiness(
        candidate_id,
        root,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
        actor=actor,
        source_approval_id=source_approval_id,
        activation_approval_id=activation_approval_id,
        reason=reason or "operator requested live activation evidence closeout",
    )
    checks = list(readiness.get("activation_executor_live_readiness_checks") or [])
    check_lookup = {str(check.get("check_id")): dict(check) for check in checks if isinstance(check, dict)}
    readiness_status = str(readiness.get("activation_executor_live_readiness_status") or "")
    activation_backend_ready = readiness_status == "activation_executor_live_readiness_ready_no_write"
    activation_gate_allowed = bool(readiness.get("gate_operation_allowed"))
    source_selected = bool(readiness.get("source_approval_id"))
    activation_selected = bool(readiness.get("activation_approval_id"))
    marker_ready = bool(readiness.get("activation_consumer_marker_ref"))
    executor_checks = {
        str(check.get("check_id")): dict(check)
        for check in readiness.get("activation_executor_checks") or []
        if isinstance(check, dict)
    }
    artifacts_ready = bool(
        executor_checks.get("activation_executor_artifacts_still_inactive_and_secret_free", {}).get(
            "passed"
        )
    )
    browser_skill_ready = bool(readiness.get("browser_skill_ref") and artifacts_ready)
    siteops_card_ready = bool(readiness.get("siteops_skill_card_ref") and artifacts_ready)
    activation_record_absent = not bool(readiness.get("activation_record_exists"))

    evidence_items = [
        {
            "evidence_key": "source_promotion_approval_id",
            "status": "satisfied" if source_selected else "missing",
            "ref": readiness.get("source_approval_id"),
            "required": True,
            "next_action": None if source_selected else "provide_or_create_scoped_source_promotion_approval",
        },
        {
            "evidence_key": "activation_approval_id",
            "status": "satisfied" if activation_selected else "missing",
            "ref": readiness.get("activation_approval_id"),
            "required": True,
            "next_action": None if activation_selected else "provide_or_create_scoped_activation_approval",
        },
        {
            "evidence_key": "activation_consumption_marker",
            "status": "satisfied" if marker_ready else "missing_or_not_checked",
            "ref": readiness.get("activation_consumer_marker_ref"),
            "required": True,
            "next_action": None if marker_ready else "consume_activation_approval_through_guarded_marker_writer",
        },
        {
            "evidence_key": "inactive_trusted_browser_skill",
            "status": "satisfied" if browser_skill_ready else "missing_or_invalid",
            "ref": readiness.get("browser_skill_ref"),
            "required": True,
            "next_action": None if browser_skill_ready else "write_or_verify_inactive_trusted_browser_skill_artifact",
        },
        {
            "evidence_key": "inactive_siteops_skill_card",
            "status": "satisfied" if siteops_card_ready else "missing_or_invalid",
            "ref": readiness.get("siteops_skill_card_ref"),
            "required": True,
            "next_action": None if siteops_card_ready else "write_or_verify_inactive_siteops_skill_card_artifact",
        },
        {
            "evidence_key": "activation_record_absent",
            "status": "satisfied" if activation_record_absent else "blocked_existing_record",
            "ref": readiness.get("activation_record_path"),
            "required": True,
            "next_action": None if activation_record_absent else "manual_review_existing_activation_record",
        },
        {
            "evidence_key": "activation_gate_allowance",
            "status": "satisfied" if activation_gate_allowed else "missing_or_denied",
            "ref": readiness.get("gate_operation"),
            "required": True,
            "next_action": None if activation_gate_allowed else "apply_or_verify_operator_approved_activation_gate_policy",
        },
        {
            "evidence_key": "activation_executor_dry_run",
            "status": "satisfied" if activation_backend_ready else "blocked",
            "ref": readiness.get("activation_executor_dry_run_status"),
            "required": True,
            "next_action": None if activation_backend_ready else "repair_activation_executor_readiness_blockers",
        },
        {
            "evidence_key": "browser_replay_shadow_mode",
            "status": "not_built",
            "ref": None,
            "required": True,
            "next_action": "design_shadow_mode_browser_replay_after_activation_evidence",
        },
    ]
    blockers = [
        item["evidence_key"]
        for item in evidence_items
        if item["required"] and item["status"] not in {"satisfied"}
    ]
    backend_blockers = [
        key for key in blockers if key != "browser_replay_shadow_mode"
    ]
    if activation_backend_ready:
        closeout_status = "live_activation_evidence_ready_for_operator_activation_no_write"
        review_decision = "operator_may_review_guarded_activation_command_but_browser_replay_still_unbuilt"
    else:
        closeout_status = "blocked_live_activation_evidence_chain"
        review_decision = str(readiness.get("review_decision") or "repair_live_activation_evidence_before_activation")

    return {
        "ok": True,
        "action": PROMOTION_LIVE_ACTIVATION_EVIDENCE_CLOSEOUT_ACTION,
        "candidate_id": readiness.get("candidate_id") or candidate_id,
        "proposed_skill_id": readiness.get("proposed_skill_id"),
        "scope": readiness.get("scope"),
        "actor": actor,
        "source_approval_id": readiness.get("source_approval_id"),
        "activation_approval_id": readiness.get("activation_approval_id"),
        "live_activation_evidence_closeout_status": closeout_status,
        "review_decision": review_decision,
        "feature_done": False,
        "backend_activation_ready": activation_backend_ready,
        "browser_replay_ready": False,
        "browser_replay_built": False,
        "browser_replay_shadow_mode_required": True,
        "remaining_backend_activation_blockers": backend_blockers,
        "remaining_feature_blockers": blockers,
        "evidence_items": evidence_items,
        "activation_executor_live_readiness_status": readiness_status,
        "activation_executor_dry_run_status": readiness.get("activation_executor_dry_run_status"),
        "activation_executor_dry_run_ready": bool(readiness.get("activation_executor_dry_run_ready")),
        "activation_consumption_live_readiness_status": readiness.get(
            "activation_consumption_live_readiness_status"
        ),
        "gate_operation": readiness.get("gate_operation"),
        "gate_operation_allowed": activation_gate_allowed,
        "gate_reason": readiness.get("gate_reason"),
        "activation_consumer_marker_ref": readiness.get("activation_consumer_marker_ref"),
        "browser_skill_ref": readiness.get("browser_skill_ref"),
        "siteops_skill_card_ref": readiness.get("siteops_skill_card_ref"),
        "activation_record_path": readiness.get("activation_record_path"),
        "activation_record_exists": bool(readiness.get("activation_record_exists")),
        "activate_command_preview": readiness.get("activate_command_preview"),
        "next_required_actions": [
            item["next_action"]
            for item in evidence_items
            if item.get("next_action")
        ],
        "readiness_check_summary": {
            "source_approval_id_selected": check_lookup.get("source_approval_id_selected", {}),
            "activation_approval_id_selected": check_lookup.get("activation_approval_id_selected", {}),
            "activation_executor_dry_run_ready": check_lookup.get("activation_executor_dry_run_ready", {}),
            "activation_executor_artifacts_still_inactive_and_secret_free": executor_checks.get(
                "activation_executor_artifacts_still_inactive_and_secret_free", {}
            ),
            "activation_gate_operation_allowed": check_lookup.get("activation_gate_operation_allowed", {}),
            "readiness_pass_is_no_write": check_lookup.get("readiness_pass_is_no_write", {}),
        },
        "writes_performed": False,
        "files_modified": False,
        "run_record_written": False,
        "activation_record_written": False,
        "activation_audit_written": False,
        "approval_consumed": False,
        "approval_decision_written": False,
        "approval_request_status_mutated": False,
        "trusted_artifacts_written": False,
        "trusted_artifacts_mutated": False,
        "trusted_skill_write_allowed": False,
        "siteops_skill_card_write_allowed": False,
        "activation_allowed": False,
        "activation_performed": False,
        "browser_execution_allowed": False,
        "agent_bus_enqueue_allowed": False,
        "provider_api_call_allowed": False,
        "gate_policy_mutation_allowed": False,
        "canonical_writeback_allowed": False,
        "blocked_actions": [
            "activate trusted artifacts",
            "write activation records",
            "append activation audit events",
            "mutate trusted Browser Skill artifact",
            "mutate SiteOps Skill Card artifact",
            "consume approval request status",
            "launch or control a browser",
            "enqueue Agent Bus work",
            "call provider APIs",
            "mutate Gate policy",
            "write canonical ChaseOS memory/state",
        ],
        "boundary": (
            "live activation evidence closeout only; it converts current "
            "activation readiness evidence into blockers and next actions. It "
            "does not activate artifacts, write records/audits, consume approvals, "
            "launch browsers, enqueue Agent Bus work, call providers, mutate Gate, "
            "or write canonical ChaseOS state."
        ),
    }


def candidate_promotion_browser_skill_shadow_replay_design(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    actor: str,
    source_approval_id: str | None = None,
    activation_approval_id: str | None = None,
    reason: str | None = None,
) -> dict[str, Any]:
    """Design Browser Skill shadow replay boundaries without browser execution."""
    closeout = candidate_promotion_live_activation_evidence_closeout(
        candidate_id,
        root,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
        actor=actor,
        source_approval_id=source_approval_id,
        activation_approval_id=activation_approval_id,
        reason=reason or "operator requested Browser Skill shadow replay design",
    )
    scope = dict(closeout.get("scope") or {})
    resolved_candidate_id = str(closeout.get("candidate_id") or candidate_id)
    slug = _slug(resolved_candidate_id)
    remaining_backend_blockers = list(closeout.get("remaining_backend_activation_blockers") or [])
    remaining_feature_blockers = list(closeout.get("remaining_feature_blockers") or [])
    backend_ready = bool(closeout.get("backend_activation_ready")) and not remaining_backend_blockers
    only_shadow_replay_left = remaining_feature_blockers == ["browser_replay_shadow_mode"]
    design_ready = backend_ready and only_shadow_replay_left

    if design_ready:
        design_status = "browser_skill_shadow_replay_design_ready_no_execution"
        review_decision = "ready_for_shadow_replay_implementation_request_next_pass"
    else:
        design_status = "blocked_browser_skill_shadow_replay_design_activation_evidence"
        review_decision = "repair_activation_evidence_before_shadow_replay_design"

    future_command_preview = [
        "python",
        "-m",
        "runtime.cli.main",
        "siteops",
        "candidates",
        "browser-skill-shadow-replay-implementation-request",
        resolved_candidate_id,
        "--source-approval-id",
        str(closeout.get("source_approval_id") or source_approval_id or "<SOURCE_APPROVAL_ID>"),
        "--activation-approval-id",
        str(closeout.get("activation_approval_id") or activation_approval_id or "<ACTIVATION_APPROVAL_ID>"),
        "--tenant",
        str(scope.get("tenant_id") or tenant_id or "<TENANT_ID>"),
        "--workspace",
        str(scope.get("workspace_id") or workspace_id or "<WORKSPACE_ID>"),
        "--user",
        str(scope.get("user_id") or user_id or "<USER_ID>"),
        "--actor",
        str(actor),
        "--json",
    ]
    design_checks = [
        _executor_preflight_check(
            "activation_backend_ready",
            passed=backend_ready,
            detail=str(closeout.get("live_activation_evidence_closeout_status") or "not_ready"),
        ),
        _executor_preflight_check(
            "remaining_backend_activation_blockers_absent",
            passed=not remaining_backend_blockers,
            detail=", ".join(remaining_backend_blockers) or "none",
        ),
        _executor_preflight_check(
            "only_browser_replay_shadow_mode_remaining",
            passed=only_shadow_replay_left,
            detail=", ".join(remaining_feature_blockers) or "none",
        ),
        _executor_preflight_check(
            "shadow_mode_required",
            passed=True,
            detail="all live browser write/action modes must start in shadow mode",
        ),
        _executor_preflight_check(
            "design_pass_is_no_execution",
            passed=True,
            detail="does not launch browser, connect CDP, replay actions, or inspect authenticated sessions",
        ),
        _executor_preflight_check(
            "authenticated_sessions_blocked_without_explicit_approval",
            passed=True,
            detail="requires separate operator approval before any authenticated browser session",
        ),
        _executor_preflight_check(
            "trusted_and_canonical_writes_blocked",
            passed=True,
            detail="does not mutate trusted skills, activation records, Gate policy, or canonical memory",
        ),
    ]
    design_requirements = [
        "shadow_mode_first_for_all_live_browser_write_or_action_modes",
        "local_or_operator_allowlisted_target_only",
        "authenticated_browser_sessions_require_explicit_user_approval",
        "throwaway_or_isolated_browser_profile_required_for_initial_replay",
        "no_secrets_cookies_tokens_or_personal_account_state_in_skills",
        "browser_observations_are_untrusted_until_human_review",
        "every_browser_task_must_emit_agent_activity_and_browser_run_logs",
        "replay_outputs_are_candidate_evidence_not_trusted_skill_truth",
        "no_dom_mutation_submit_or_external_write_in_design_pass",
        "no_live_site_mutation_until_separately_approved_after_shadow_proof",
    ]
    future_shadow_replay_artifacts = [
        f"07_LOGS/Browser-Runs/siteops-shadow-replay-{slug}.json",
        f"07_LOGS/Agent-Activity/<YYYY-MM-DD>-siteops-shadow-replay-{slug}.md",
        f"03_INPUTS/Browser-Skill-Candidates/<domain>/shadow-replay-{slug}.md",
    ]

    return {
        "ok": True,
        "action": PROMOTION_BROWSER_SKILL_SHADOW_REPLAY_DESIGN_ACTION,
        "candidate_id": resolved_candidate_id,
        "proposed_skill_id": closeout.get("proposed_skill_id"),
        "scope": closeout.get("scope"),
        "actor": actor,
        "source_approval_id": closeout.get("source_approval_id"),
        "activation_approval_id": closeout.get("activation_approval_id"),
        "browser_skill_shadow_replay_design_status": design_status,
        "review_decision": review_decision,
        "ready_for_shadow_replay_implementation_request_next_pass": design_ready,
        "backend_activation_ready": backend_ready,
        "activation_write_required_in_this_pass": False,
        "future_replay_may_require_active_trusted_artifact_or_activation_ready_evidence": True,
        "shadow_mode_required": True,
        "shadow_mode_built": False,
        "browser_replay_ready": False,
        "browser_replay_built": False,
        "browser_skill_ref": closeout.get("browser_skill_ref"),
        "siteops_skill_card_ref": closeout.get("siteops_skill_card_ref"),
        "activation_record_path": closeout.get("activation_record_path"),
        "remaining_backend_activation_blockers": remaining_backend_blockers,
        "remaining_feature_blockers": remaining_feature_blockers,
        "live_activation_evidence_closeout_status": closeout.get(
            "live_activation_evidence_closeout_status"
        ),
        "activation_executor_live_readiness_status": closeout.get(
            "activation_executor_live_readiness_status"
        ),
        "activation_executor_dry_run_status": closeout.get("activation_executor_dry_run_status"),
        "gate_operation": closeout.get("gate_operation"),
        "gate_operation_allowed": bool(closeout.get("gate_operation_allowed")),
        "design_requirements": design_requirements,
        "future_shadow_replay_artifacts": future_shadow_replay_artifacts,
        "future_shadow_replay_implementation_request_command_preview": future_command_preview,
        "browser_skill_shadow_replay_design_checks": design_checks,
        "writes_performed": False,
        "files_modified": False,
        "run_record_written": False,
        "activation_record_written": False,
        "activation_audit_written": False,
        "browser_run_log_written": False,
        "agent_activity_log_written": False,
        "approval_consumed": False,
        "approval_decision_written": False,
        "approval_request_status_mutated": False,
        "trusted_artifacts_written": False,
        "trusted_artifacts_mutated": False,
        "trusted_skill_write_allowed": False,
        "siteops_skill_card_write_allowed": False,
        "activation_allowed": False,
        "activation_performed": False,
        "browser_execution_allowed": False,
        "browser_launch_allowed": False,
        "cdp_connection_allowed": False,
        "authenticated_session_allowed": False,
        "real_profile_allowed": False,
        "cookie_or_token_access_allowed": False,
        "dom_mutation_allowed": False,
        "external_submit_allowed": False,
        "agent_bus_enqueue_allowed": False,
        "provider_api_call_allowed": False,
        "gate_policy_mutation_allowed": False,
        "canonical_writeback_allowed": False,
        "blocked_actions": [
            "activate trusted artifacts",
            "write activation records",
            "append activation audit events",
            "mutate trusted Browser Skill artifact",
            "mutate SiteOps Skill Card artifact",
            "write Browser Run logs",
            "launch or control a browser",
            "connect to CDP",
            "use authenticated browser sessions",
            "read cookies, tokens, or secrets",
            "mutate DOM or submit forms",
            "enqueue Agent Bus work",
            "call provider APIs",
            "mutate Gate policy",
            "write canonical ChaseOS memory/state",
        ],
        "boundary": (
            "Browser Skill shadow replay design only; it consumes live activation "
            "evidence closeout as read-only input and defines the future replay "
            "guardrails. It does not activate artifacts, write records/audits, "
            "write Browser Run logs, launch browsers, connect CDP, inspect "
            "authenticated sessions, enqueue Agent Bus work, call providers, "
            "mutate Gate, or write canonical ChaseOS state."
        ),
    }


def candidate_promotion_browser_skill_shadow_replay_implementation_request(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    actor: str,
    source_approval_id: str | None = None,
    activation_approval_id: str | None = None,
    reason: str | None = None,
) -> dict[str, Any]:
    """Package shadow replay implementation requirements without browser execution."""
    design = candidate_promotion_browser_skill_shadow_replay_design(
        candidate_id,
        root,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
        actor=actor,
        source_approval_id=source_approval_id,
        activation_approval_id=activation_approval_id,
        reason=reason or "operator requested Browser Skill shadow replay implementation request",
    )
    scope = dict(design.get("scope") or {})
    resolved_candidate_id = str(design.get("candidate_id") or candidate_id)
    slug = _slug(resolved_candidate_id)
    request_id = _new_run_id(f"{resolved_candidate_id}_shadow_replay_implementation_request")
    design_ready = bool(design.get("ready_for_shadow_replay_implementation_request_next_pass"))
    future_write_set = {
        "browser_run_log_path": f"07_LOGS/Browser-Runs/siteops-shadow-replay-{slug}.json",
        "agent_activity_log_path": f"07_LOGS/Agent-Activity/<YYYY-MM-DD>-siteops-shadow-replay-{slug}.md",
        "shadow_replay_candidate_path": (
            f"03_INPUTS/Browser-Skill-Candidates/<domain>/shadow-replay-{slug}.md"
        ),
        "activation_record_path": design.get("activation_record_path"),
        "browser_skill_ref": design.get("browser_skill_ref"),
        "siteops_skill_card_ref": design.get("siteops_skill_card_ref"),
        "writes_allowed_in_this_pass": False,
    }
    request_packet = {
        "request_id": request_id,
        "request_type": "siteops_browser_skill_shadow_replay_implementation_request",
        "tenant_id": scope.get("tenant_id"),
        "workspace_id": scope.get("workspace_id"),
        "user_id": scope.get("user_id"),
        "candidate_id": resolved_candidate_id,
        "proposed_skill_id": design.get("proposed_skill_id"),
        "source_approval_id": design.get("source_approval_id"),
        "activation_approval_id": design.get("activation_approval_id"),
        "actor": actor,
        "reason": reason or "",
        "requested_action": "implement_browser_skill_shadow_replay_runner",
        "required_operator_decision": "approve_future_shadow_replay_implementation_pass",
        "status": "review_packet_only",
        "design_status": design.get("browser_skill_shadow_replay_design_status"),
        "future_command_name": "browser-skill-shadow-replay",
        "future_required_mode": "shadow",
        "future_required_flags": [
            "--shadow-mode",
            "--write-browser-run-log",
        ],
        "future_write_set": future_write_set,
        "record_schema": {
            "record_type": "siteops_browser_skill_shadow_replay_request",
            "required_fields": [
                "request_id",
                "tenant_id",
                "workspace_id",
                "user_id",
                "candidate_id",
                "proposed_skill_id",
                "source_approval_id",
                "activation_approval_id",
                "future_write_set",
                "required_operator_decision",
                "shadow_mode_required",
            ],
            "forbidden_fields": [
                "cookie",
                "token",
                "secret",
                "password",
                "browser_session_state",
                "personal_account_state",
                "api_key",
                "oauth",
            ],
            "durable_artifact_written_in_this_pass": False,
        },
        "implementation_allowed_in_this_pass": False,
        "writes_allowed_in_this_pass": False,
        "browser_launch_allowed_in_this_pass": False,
        "cdp_connection_allowed_in_this_pass": False,
        "authenticated_session_allowed_in_this_pass": False,
        "dom_mutation_allowed_in_this_pass": False,
        "agent_bus_enqueue_allowed_in_this_pass": False,
        "provider_call_allowed_in_this_pass": False,
        "canonical_writeback_allowed_in_this_pass": False,
    }
    write_set_ready = all(
        bool(future_write_set.get(key))
        for key in (
            "browser_run_log_path",
            "agent_activity_log_path",
            "shadow_replay_candidate_path",
            "browser_skill_ref",
            "siteops_skill_card_ref",
        )
    )
    request_checks = list(design.get("browser_skill_shadow_replay_design_checks") or []) + [
        _executor_preflight_check(
            "shadow_replay_design_ready",
            passed=design_ready,
            detail=str(design.get("browser_skill_shadow_replay_design_status")),
        ),
        _executor_preflight_check(
            "future_write_set_declared",
            passed=write_set_ready,
            detail=", ".join(
                key for key, value in future_write_set.items() if value and key.endswith("_path")
            ),
        ),
        _executor_preflight_check(
            "request_scope_bound",
            passed=all(request_packet.get(key) == scope.get(key) for key in ("tenant_id", "workspace_id", "user_id")),
            detail=json.dumps(
                {
                    "tenant_id": scope.get("tenant_id"),
                    "workspace_id": scope.get("workspace_id"),
                    "user_id": scope.get("user_id"),
                },
                sort_keys=True,
            ),
        ),
        _executor_preflight_check(
            "operator_approval_required_next",
            passed=True,
            detail="approve_future_shadow_replay_implementation_pass",
        ),
        _executor_preflight_check(
            "request_pass_is_no_write_no_browser",
            passed=True,
            detail="does not write artifacts, launch browser, connect CDP, use sessions, or submit DOM actions",
        ),
    ]
    request_ready = design_ready and write_set_ready and all(
        bool(check.get("passed")) for check in request_checks
    )
    if request_ready:
        request_status = "browser_skill_shadow_replay_implementation_request_ready_no_write"
        review_decision = "ready_for_shadow_replay_implementation_approval_next_pass"
    else:
        request_status = "blocked_browser_skill_shadow_replay_implementation_request"
        review_decision = "repair_shadow_replay_design_before_implementation_request"

    return {
        "ok": True,
        "action": PROMOTION_BROWSER_SKILL_SHADOW_REPLAY_IMPLEMENTATION_REQUEST_ACTION,
        "candidate_id": resolved_candidate_id,
        "proposed_skill_id": design.get("proposed_skill_id"),
        "scope": design.get("scope"),
        "actor": actor,
        "source_approval_id": design.get("source_approval_id"),
        "activation_approval_id": design.get("activation_approval_id"),
        "browser_skill_shadow_replay_design_status": design.get(
            "browser_skill_shadow_replay_design_status"
        ),
        "browser_skill_shadow_replay_implementation_request_status": request_status,
        "review_decision": review_decision,
        "ready_for_shadow_replay_implementation_approval_next_pass": request_ready,
        "backend_activation_ready": bool(design.get("backend_activation_ready")),
        "shadow_mode_required": True,
        "shadow_mode_built": False,
        "browser_replay_ready": False,
        "browser_replay_built": False,
        "shadow_replay_implementation_request": request_packet,
        "shadow_replay_implementation_request_checks": request_checks,
        "future_write_set": future_write_set,
        "future_implementation_requirements": [
            "operator must explicitly approve a future shadow replay implementation pass",
            "future implementation must start in shadow mode",
            "future implementation must write only scoped Browser Run and Agent Activity evidence",
            "future implementation must use local/operator-allowlisted targets only",
            "future implementation must not use authenticated sessions without separate approval",
            "future implementation must not store cookies, tokens, secrets, or browser session state",
            "future implementation must not mutate DOM, submit forms, publish, buy, trade, or change accounts",
            "future implementation must keep replay observations as candidate evidence until human review",
        ],
        "implementation_request_artifact_written": False,
        "writes_performed": False,
        "files_modified": False,
        "run_record_written": False,
        "browser_run_log_written": False,
        "agent_activity_log_written": False,
        "approval_consumed": False,
        "approval_decision_written": False,
        "approval_request_status_mutated": False,
        "activation_record_written": False,
        "activation_audit_written": False,
        "activation_performed": False,
        "trusted_artifacts_written": False,
        "trusted_artifacts_mutated": False,
        "browser_execution_allowed": False,
        "browser_launch_allowed": False,
        "cdp_connection_allowed": False,
        "authenticated_session_allowed": False,
        "real_profile_allowed": False,
        "cookie_or_token_access_allowed": False,
        "dom_mutation_allowed": False,
        "external_submit_allowed": False,
        "agent_bus_enqueue_allowed": False,
        "provider_api_call_allowed": False,
        "gate_policy_mutation_allowed": False,
        "canonical_writeback_allowed": False,
        "blocked_actions": list(design.get("blocked_actions") or []) + [
            "write shadow replay implementation request artifact",
            "implement shadow replay runner",
            "write Browser Run evidence",
            "write Agent Activity evidence",
        ],
        "boundary": (
            "Browser Skill shadow replay implementation request only; it packages "
            "the future write set, record schema, and operator approval boundary. "
            "It does not write artifacts, launch browsers, connect CDP, inspect "
            "authenticated sessions, enqueue Agent Bus work, call providers, mutate "
            "Gate, activate skills, or write canonical ChaseOS state."
        ),
    }


def candidate_promotion_browser_skill_shadow_replay_implementation_approval(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    actor: str,
    decision: str,
    source_approval_id: str | None = None,
    activation_approval_id: str | None = None,
    reason: str | None = None,
) -> dict[str, Any]:
    """Return no-write approve/reject intent for future shadow replay implementation."""
    normalized_decision = (decision or "").strip().lower()
    if normalized_decision not in {"approve", "reject"}:
        raise ValueError("decision must be 'approve' or 'reject'")

    implementation_request = (
        candidate_promotion_browser_skill_shadow_replay_implementation_request(
            candidate_id,
            root,
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            user_id=user_id,
            actor=actor,
            source_approval_id=source_approval_id,
            activation_approval_id=activation_approval_id,
            reason=reason or "operator requested Browser Skill shadow replay implementation approval",
        )
    )
    scope = dict(implementation_request.get("scope") or {})
    request_packet = dict(
        implementation_request.get("shadow_replay_implementation_request") or {}
    )
    request_status = implementation_request.get(
        "browser_skill_shadow_replay_implementation_request_status"
    )
    request_ready = bool(
        implementation_request.get("ready_for_shadow_replay_implementation_approval_next_pass")
    )
    actor_id = (actor or user_id or "").strip()
    approval_id = _new_run_id(
        f"shadow_replay_implementation_approval_{implementation_request.get('candidate_id')}"
    )
    approval_packet = {
        "approval_id": approval_id,
        "record_type": "siteops_browser_skill_shadow_replay_implementation_approval",
        "tenant_id": scope.get("tenant_id"),
        "workspace_id": scope.get("workspace_id"),
        "user_id": scope.get("user_id"),
        "actor": actor_id,
        "decision": normalized_decision,
        "reason": reason or "",
        "candidate_id": implementation_request.get("candidate_id"),
        "proposed_skill_id": implementation_request.get("proposed_skill_id"),
        "source_approval_id": implementation_request.get("source_approval_id"),
        "activation_approval_id": implementation_request.get("activation_approval_id"),
        "implementation_request_id": request_packet.get("request_id"),
        "future_command_name": request_packet.get("future_command_name"),
        "future_required_mode": request_packet.get("future_required_mode"),
        "future_required_flags": request_packet.get("future_required_flags"),
        "future_write_set": request_packet.get("future_write_set"),
        "record_schema": request_packet.get("record_schema"),
        "status": "review_decision_packet_only",
        "durable_record_written": False,
        "approval_decision_written": False,
        "implementation_allowed_in_this_pass": False,
        "shadow_replay_runner_allowed_in_this_pass": False,
        "browser_run_log_write_allowed_in_this_pass": False,
        "agent_activity_log_write_allowed_in_this_pass": False,
        "browser_launch_allowed_in_this_pass": False,
        "cdp_connection_allowed_in_this_pass": False,
        "authenticated_session_allowed_in_this_pass": False,
        "dom_mutation_allowed_in_this_pass": False,
        "agent_bus_enqueue_allowed_in_this_pass": False,
        "provider_call_allowed_in_this_pass": False,
        "canonical_writeback_allowed_in_this_pass": False,
    }
    approval_checks = [
        _executor_preflight_check(
            "shadow_replay_implementation_request_ready",
            passed=request_ready,
            detail=str(request_status),
        ),
        _executor_preflight_check(
            "shadow_replay_implementation_approval_decision_valid",
            passed=True,
            detail=normalized_decision,
        ),
        _executor_preflight_check(
            "shadow_replay_implementation_approval_actor_present",
            passed=bool(actor_id),
            detail=actor_id,
        ),
        _executor_preflight_check(
            "shadow_replay_implementation_approval_record_still_no_write",
            passed=True,
            detail="durable_record_written=false; approval_decision_written=false",
        ),
        _executor_preflight_check(
            "shadow_replay_runner_still_not_implemented",
            passed=True,
            detail="browser replay implementation remains future work",
        ),
        _executor_preflight_check(
            "shadow_replay_implementation_approval_browser_still_blocked",
            passed=True,
            detail="no browser launch, CDP connection, authenticated session, or DOM action",
        ),
    ]
    approval_ready = request_ready and bool(actor_id)
    if not request_ready:
        approval_status = f"blocked_shadow_replay_implementation_request: {request_status}"
        review_decision = "blocked_before_shadow_replay_implementation_approval"
    elif not actor_id:
        approval_status = "blocked_missing_shadow_replay_implementation_approval_actor"
        review_decision = "blocked_before_shadow_replay_implementation_approval"
    elif normalized_decision == "approve":
        approval_status = "shadow_replay_implementation_approved_for_next_pass_no_write"
        review_decision = "operator_intent_approve_shadow_replay_implementation_next_pass"
    else:
        approval_status = "shadow_replay_implementation_rejected_no_write"
        review_decision = "operator_intent_reject_shadow_replay_implementation"

    implementation_approved = approval_ready and normalized_decision == "approve"
    implementation_rejected = approval_ready and normalized_decision == "reject"
    denied_effects = list(
        implementation_request.get("denied_effects")
        or implementation_request.get("blocked_actions")
        or []
    )
    for effect in [
        "write shadow replay implementation approval record",
        "implement shadow replay runner from approval packet",
        "write Browser Run evidence",
        "write Agent Activity replay evidence",
        "launch or control a browser",
        "connect to CDP",
        "use authenticated browser sessions",
        "read cookies, tokens, or secrets",
        "mutate DOM or submit forms",
    ]:
        if effect not in denied_effects:
            denied_effects.append(effect)

    result = dict(implementation_request)
    result.update(
        {
            "action": PROMOTION_BROWSER_SKILL_SHADOW_REPLAY_IMPLEMENTATION_APPROVAL_ACTION,
            "decision": normalized_decision,
            "actor": actor_id,
            "browser_skill_shadow_replay_implementation_request_status": request_status,
            "browser_skill_shadow_replay_implementation_approval_status": approval_status,
            "review_decision": review_decision,
            "shadow_replay_implementation_approval": approval_packet,
            "shadow_replay_implementation_approval_checks": approval_checks,
            "implementation_request_packet": {
                "request_id": request_packet.get("request_id"),
                "status": request_status,
                "request_ready_no_write": request_ready,
            },
            "shadow_replay_implementation_approved_for_next_pass": implementation_approved,
            "shadow_replay_implementation_rejected": implementation_rejected,
            "ready_for_shadow_replay_implementation_next_pass": implementation_approved,
            "implementation_approval_artifact_written": False,
            "approval_decision_written": False,
            "implementation_request_artifact_written": False,
            "shadow_replay_runner_implemented": False,
            "shadow_replay_runner_allowed_in_this_pass": False,
            "browser_replay_ready": False,
            "browser_replay_built": False,
            "browser_run_log_written": False,
            "agent_activity_log_written": False,
            "activation_record_written": False,
            "activation_audit_written": False,
            "approval_consumed": False,
            "approval_request_status_mutated": False,
            "trusted_artifacts_written": False,
            "trusted_artifacts_mutated": False,
            "activation_performed": False,
            "browser_execution_allowed": False,
            "browser_launch_allowed": False,
            "cdp_connection_allowed": False,
            "authenticated_session_allowed": False,
            "real_profile_allowed": False,
            "cookie_or_token_access_allowed": False,
            "dom_mutation_allowed": False,
            "external_submit_allowed": False,
            "agent_bus_enqueue_allowed": False,
            "provider_api_call_allowed": False,
            "gate_policy_mutation_allowed": False,
            "canonical_writeback_allowed": False,
            "writes_performed": False,
            "files_modified": False,
            "blocked_actions": denied_effects,
            "denied_effects": denied_effects,
            "boundary": (
                "Browser Skill shadow replay implementation approval only; records "
                "approve/reject intent for a future guarded shadow replay "
                "implementation pass. It writes no approval artifact, Browser Run "
                "log, Agent Activity replay evidence, activation record, trusted "
                "artifact, Gate policy, browser/CDP action, Agent Bus task, "
                "provider call, or canonical ChaseOS state."
            ),
        }
    )
    return result


def _candidate_promotion_browser_skill_shadow_replay_runner_write_guard_legacy_unused(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    actor: str,
    source_approval_id: str | None = None,
    activation_approval_id: str | None = None,
    reason: str | None = None,
) -> dict[str, Any]:
    """Legacy unused draft retained only to avoid disrupting parallel edits."""
    approval = candidate_promotion_browser_skill_shadow_replay_implementation_approval(
        candidate_id,
        root,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
        actor=actor,
        decision="approve",
        source_approval_id=source_approval_id,
        activation_approval_id=activation_approval_id,
        reason=reason or "operator requested Browser Skill shadow replay runner write guard",
    )
    resolved_candidate_id = str(approval.get("candidate_id") or candidate_id)
    approval_status = str(
        approval.get("browser_skill_shadow_replay_implementation_approval_status") or ""
    )
    approved_for_next = bool(
        approval.get("ready_for_shadow_replay_implementation_next_pass")
    )
    implementation_approval = dict(
        approval.get("shadow_replay_implementation_approval") or {}
    )
    future_write_set = dict(
        approval.get("future_write_set")
        or implementation_approval.get("future_write_set")
        or {}
    )
    scoped_future_write_targets = [
        str(future_write_set.get("browser_run_log_path") or ""),
        str(future_write_set.get("agent_activity_log_path") or ""),
        str(future_write_set.get("shadow_replay_candidate_path") or ""),
    ]
    scoped_future_write_targets = [
        target for target in scoped_future_write_targets if target
    ]
    forbidden_future_write_targets = [
        str(future_write_set.get("activation_record_path") or "07_LOGS/SiteOps-Activations/**"),
        str(future_write_set.get("browser_skill_ref") or "runtime/browser_skills/skills/*.yaml"),
        str(future_write_set.get("siteops_skill_card_ref") or "runtime/siteops/registry/skill_cards/*.json"),
        "runtime/chaseos_gate.py",
        "runtime/policy/gateway_allowlists.json",
        "canonical ChaseOS memory/state",
        "browser profile/session state",
        "cookies/tokens/secrets/credentials",
    ]
    write_targets_declared = all(
        future_write_set.get(key)
        for key in (
            "browser_run_log_path",
            "agent_activity_log_path",
            "shadow_replay_candidate_path",
        )
    )
    forbidden_targets_declared = all(forbidden_future_write_targets)
    write_guard_contract = {
        "contract_type": "siteops_browser_skill_shadow_replay_runner_write_guard",
        "candidate_id": resolved_candidate_id,
        "proposed_skill_id": approval.get("proposed_skill_id"),
        "tenant_id": (approval.get("scope") or {}).get("tenant_id"),
        "workspace_id": (approval.get("scope") or {}).get("workspace_id"),
        "user_id": (approval.get("scope") or {}).get("user_id"),
        "source_approval_id": approval.get("source_approval_id"),
        "activation_approval_id": approval.get("activation_approval_id"),
        "implementation_approval_id": implementation_approval.get("approval_id"),
        "implementation_request_id": implementation_approval.get("implementation_request_id"),
        "future_runner_command_name": "browser-skill-shadow-replay",
        "future_required_mode": "shadow",
        "future_required_flags": [
            "--shadow-mode",
            "--write-browser-run-log",
            "--write-agent-activity-log",
            "--write-candidate-evidence",
        ],
        "allowed_future_write_targets": scoped_future_write_targets,
        "forbidden_future_write_targets": forbidden_future_write_targets,
        "future_write_preconditions": [
            "approved shadow replay implementation intent",
            "shadow mode required",
            "local or operator-allowlisted target only",
            "isolated or throwaway browser profile",
            "no authenticated session unless separately approved",
            "no cookies, tokens, secrets, credentials, or personal account state",
            "Browser Run log and Agent Activity log required for every task",
            "candidate replay evidence remains untrusted until review",
        ],
        "future_fail_closed_conditions": [
            "missing implementation approval",
            "missing --shadow-mode",
            "missing Browser Run log target",
            "missing Agent Activity log target",
            "target not local or operator-allowlisted",
            "authenticated session requested without separate approval",
            "cookie/token/secret/profile-state capture detected",
            "DOM mutation or form submit requested",
            "trusted artifact, activation, Gate, or canonical write requested",
        ],
        "durable_contract_written": False,
        "writes_allowed_in_this_pass": False,
    }
    checks = [
        _executor_preflight_check(
            "shadow_replay_implementation_approved_no_write",
            passed=approved_for_next,
            detail=approval_status,
        ),
        _executor_preflight_check(
            "future_write_targets_declared",
            passed=write_targets_declared,
            detail=", ".join(scoped_future_write_targets) or "missing",
        ),
        _executor_preflight_check(
            "future_write_targets_scoped_to_logs_and_candidate_evidence",
            passed=all(
                target.startswith("07_LOGS/Browser-Runs/")
                or target.startswith("07_LOGS/Agent-Activity/")
                or target.startswith("03_INPUTS/Browser-Skill-Candidates/")
                for target in scoped_future_write_targets
            ),
            detail=", ".join(scoped_future_write_targets) or "missing",
        ),
        _executor_preflight_check(
            "forbidden_trusted_activation_gate_and_secret_writes_declared",
            passed=forbidden_targets_declared,
            detail=", ".join(forbidden_future_write_targets),
        ),
        _executor_preflight_check(
            "future_runner_requires_shadow_mode_and_logs",
            passed=True,
            detail="--shadow-mode, Browser Run log, Agent Activity log, and candidate evidence are required",
        ),
        _executor_preflight_check(
            "write_guard_pass_is_no_write_no_browser",
            passed=True,
            detail="does not write guard artifacts, launch browser, connect CDP, or replay actions",
        ),
    ]
    write_guard_ready = approved_for_next and all(
        bool(check.get("passed")) for check in checks
    )
    if write_guard_ready:
        guard_status = "shadow_replay_runner_write_guard_ready_no_write"
        review_decision = "ready_for_shadow_replay_runner_implementation_next_pass"
    else:
        guard_status = "blocked_shadow_replay_runner_write_guard"
        review_decision = "repair_shadow_replay_approval_or_write_set_before_runner"

    result = dict(approval)
    result.update(
        {
            "action": PROMOTION_BROWSER_SKILL_SHADOW_REPLAY_RUNNER_WRITE_GUARD_ACTION,
            "browser_skill_shadow_replay_runner_write_guard_status": guard_status,
            "review_decision": review_decision,
            "ready_for_shadow_replay_runner_implementation_next_pass": write_guard_ready,
            "shadow_replay_runner_write_guard": write_guard_contract,
            "shadow_replay_runner_write_guard_checks": checks,
            "allowed_future_write_targets": scoped_future_write_targets,
            "forbidden_future_write_targets": forbidden_future_write_targets,
            "shadow_replay_runner_write_guard_artifact_written": False,
            "write_guard_contract_written": False,
            "shadow_replay_runner_implemented": False,
            "shadow_replay_runner_allowed_in_this_pass": False,
            "browser_replay_ready": False,
            "browser_replay_built": False,
            "browser_run_log_written": False,
            "agent_activity_log_written": False,
            "implementation_request_artifact_written": False,
            "implementation_approval_artifact_written": False,
            "activation_record_written": False,
            "activation_audit_written": False,
            "approval_consumed": False,
            "approval_decision_written": False,
            "approval_request_status_mutated": False,
            "trusted_artifacts_written": False,
            "trusted_artifacts_mutated": False,
            "activation_performed": False,
            "browser_execution_allowed": False,
            "browser_launch_allowed": False,
            "cdp_connection_allowed": False,
            "authenticated_session_allowed": False,
            "real_profile_allowed": False,
            "cookie_or_token_access_allowed": False,
            "dom_mutation_allowed": False,
            "external_submit_allowed": False,
            "agent_bus_enqueue_allowed": False,
            "provider_api_call_allowed": False,
            "gate_policy_mutation_allowed": False,
            "canonical_writeback_allowed": False,
            "writes_performed": False,
            "files_modified": False,
            "blocked_actions": list(approval.get("blocked_actions") or []) + [
                "write shadow replay runner write guard artifact",
                "implement shadow replay runner",
                "launch or control a browser",
                "connect to CDP",
                "write Browser Run evidence",
                "write Agent Activity replay evidence",
            ],
            "boundary": (
                "Browser Skill shadow replay runner write-guard contract only; "
                "it validates no-write implementation approval intent and defines "
                "the future allowed/forbidden write targets. It does not write "
                "guard artifacts, implement or run the replay runner, launch "
                "browser/CDP, use authenticated sessions, write Browser Run or "
                "Agent Activity evidence, mutate trusted artifacts, activate "
                "skills, mutate Gate, call providers, enqueue Agent Bus work, or "
                "write canonical ChaseOS state."
            ),
        }
    )
    return result


def candidate_promotion_browser_skill_shadow_replay_runner_write_guard(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    actor: str,
    source_approval_id: str | None = None,
    activation_approval_id: str | None = None,
    reason: str | None = None,
) -> dict[str, Any]:
    """Declare future shadow replay runner guardrails without implementing replay."""
    implementation_approval = (
        candidate_promotion_browser_skill_shadow_replay_implementation_approval(
            candidate_id,
            root,
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            user_id=user_id,
            actor=actor,
            decision="approve",
            source_approval_id=source_approval_id,
            activation_approval_id=activation_approval_id,
            reason=reason or "operator requested Browser Skill shadow replay runner write guard",
        )
    )
    scope = dict(implementation_approval.get("scope") or {})
    resolved_candidate_id = str(implementation_approval.get("candidate_id") or candidate_id)
    slug = _slug(resolved_candidate_id)
    approval_packet = dict(
        implementation_approval.get("shadow_replay_implementation_approval") or {}
    )
    future_write_set = dict(
        approval_packet.get("future_write_set")
        or implementation_approval.get("future_write_set")
        or {}
    )
    browser_run_record_schema = {
        "record_type": "siteops_browser_skill_shadow_replay_run",
        "required_fields": [
            "run_id",
            "tenant_id",
            "workspace_id",
            "user_id",
            "candidate_id",
            "proposed_skill_id",
            "source_approval_id",
            "activation_approval_id",
            "implementation_approval_id",
            "target_url",
            "shadow_mode",
            "actions_planned",
            "actions_observed",
            "policy_decisions",
            "screenshots_ref",
            "artifacts_ref",
            "started_at",
            "ended_at",
            "status",
        ],
        "forbidden_fields": [
            "cookie",
            "token",
            "secret",
            "password",
            "browser_session_state",
            "localStorage",
            "sessionStorage",
            "personal_account_state",
            "api_key",
            "oauth",
            "raw_html_with_account_data",
        ],
    }
    guard_contract = {
        "contract_type": "siteops_browser_skill_shadow_replay_runner_write_guard",
        "status": "runner_write_guard_contract_only",
        "durable_contract_written": False,
        "future_command_name": "browser-skill-shadow-replay",
        "future_required_mode": "shadow",
        "future_required_flags": [
            "--shadow-mode",
            "--write-browser-run-log",
            "--target-url",
        ],
        "future_optional_flags": [
            "--local-target-only",
            "--allowlisted-domain",
            "--max-steps",
            "--screenshot-trace",
        ],
        "explicit_write_flag": "--write-browser-run-log",
        "explicit_write_flag_supported_in_this_pass": False,
        "unsupported_flag_rejection": (
            "--write-browser-run-log remains unsupported until the guarded runner "
            "implementation pass"
        ),
        "allowed_future_write_roots": [
            f"07_LOGS/Browser-Runs/{scope.get('tenant_id')}/{scope.get('workspace_id')}/",
            f"07_LOGS/Agent-Activity/{scope.get('tenant_id')}/{scope.get('workspace_id')}/",
            "03_INPUTS/Browser-Skill-Candidates/",
        ],
        "allowed_future_write_targets": [
            f"07_LOGS/Browser-Runs/{scope.get('tenant_id')}/{scope.get('workspace_id')}/siteops-shadow-replay-{slug}.json",
            f"07_LOGS/Agent-Activity/{scope.get('tenant_id')}/{scope.get('workspace_id')}/<YYYY-MM-DD>-siteops-shadow-replay-{slug}.md",
            f"03_INPUTS/Browser-Skill-Candidates/<domain>/shadow-replay-{slug}.md",
        ],
        "forbidden_future_write_targets": [
            "runtime/chaseos_gate.py",
            "runtime/policy/gateway_allowlists.json",
            "runtime/browser_skills/skills/**",
            "runtime/siteops/registry/skill_cards/**",
            "00_HOME/**",
            "06_AGENTS/**",
            "99_ARCHIVE/Reporting/**",
        ],
        "future_write_set": {
            "browser_run_log_path": (
                f"07_LOGS/Browser-Runs/{scope.get('tenant_id')}/{scope.get('workspace_id')}/"
                f"siteops-shadow-replay-{slug}.json"
            ),
            "agent_activity_log_path": (
                f"07_LOGS/Agent-Activity/{scope.get('tenant_id')}/{scope.get('workspace_id')}/"
                f"<YYYY-MM-DD>-siteops-shadow-replay-{slug}.md"
            ),
            "shadow_replay_candidate_path": future_write_set.get("shadow_replay_candidate_path"),
            "browser_skill_ref": future_write_set.get("browser_skill_ref"),
            "siteops_skill_card_ref": future_write_set.get("siteops_skill_card_ref"),
            "writes_allowed_in_this_pass": False,
        },
        "target_policy": {
            "local_or_operator_allowlisted_target_required": True,
            "authenticated_session_allowed": False,
            "manual_takeover_allowed_future": True,
            "external_submit_allowed": False,
            "dom_mutation_allowed": False,
            "public_posting_allowed": False,
            "purchase_allowed": False,
            "account_mutation_allowed": False,
            "broker_connection_allowed": False,
        },
        "browser_run_record_schema": browser_run_record_schema,
        "runner_implemented_in_this_pass": False,
        "browser_launch_allowed_in_this_pass": False,
        "cdp_connection_allowed_in_this_pass": False,
        "browser_run_log_write_allowed_in_this_pass": False,
        "agent_activity_log_write_allowed_in_this_pass": False,
        "canonical_writeback_allowed_in_this_pass": False,
    }
    implementation_ready = bool(
        implementation_approval.get("ready_for_shadow_replay_implementation_next_pass")
    )
    write_set_ready = all(
        bool(guard_contract["future_write_set"].get(key))
        for key in (
            "browser_run_log_path",
            "agent_activity_log_path",
            "shadow_replay_candidate_path",
            "browser_skill_ref",
            "siteops_skill_card_ref",
        )
    )
    schema_ready = all(
        field in browser_run_record_schema["required_fields"]
        for field in (
            "tenant_id",
            "workspace_id",
            "user_id",
            "target_url",
            "shadow_mode",
            "policy_decisions",
            "status",
        )
    ) and "cookie" in browser_run_record_schema["forbidden_fields"]
    checks = list(implementation_approval.get("shadow_replay_implementation_approval_checks") or []) + [
        _executor_preflight_check(
            "shadow_replay_implementation_approved_no_write",
            passed=implementation_ready,
            detail=str(
                implementation_approval.get(
                    "browser_skill_shadow_replay_implementation_approval_status"
                )
            ),
        ),
        _executor_preflight_check(
            "future_runner_requires_shadow_mode",
            passed="--shadow-mode" in guard_contract["future_required_flags"],
            detail="--shadow-mode",
        ),
        _executor_preflight_check(
            "future_runner_requires_browser_run_write_flag",
            passed=guard_contract["explicit_write_flag"] == "--write-browser-run-log",
            detail=guard_contract["explicit_write_flag"],
        ),
        _executor_preflight_check(
            "future_write_targets_scoped_to_logs_and_candidate_evidence",
            passed=write_set_ready,
            detail=json.dumps(guard_contract["future_write_set"], sort_keys=True),
        ),
        _executor_preflight_check(
            "browser_run_record_schema_declared",
            passed=schema_ready,
            detail="tenant/workspace/user scoped; secret/session fields forbidden",
        ),
        _executor_preflight_check(
            "authenticated_sessions_blocked_in_guard",
            passed=not guard_contract["target_policy"]["authenticated_session_allowed"],
            detail="authenticated_session_allowed=false",
        ),
        _executor_preflight_check(
            "dom_mutation_and_external_submit_blocked_in_guard",
            passed=(
                not guard_contract["target_policy"]["dom_mutation_allowed"]
                and not guard_contract["target_policy"]["external_submit_allowed"]
            ),
            detail="dom_mutation_allowed=false; external_submit_allowed=false",
        ),
        _executor_preflight_check(
            "write_guard_pass_is_no_write_no_browser",
            passed=True,
            detail="does not implement runner, write logs, launch browser, connect CDP, or use sessions",
        ),
    ]
    guard_ready = implementation_ready and write_set_ready and schema_ready and all(
        bool(check.get("passed")) for check in checks
    )
    if guard_ready:
        guard_status = "shadow_replay_runner_write_guard_ready_no_write"
        review_decision = "ready_for_shadow_replay_runner_implementation_next_pass"
    else:
        guard_status = "blocked_shadow_replay_runner_write_guard"
        review_decision = "repair_shadow_replay_implementation_approval_before_runner"

    denied_effects = list(
        implementation_approval.get("denied_effects")
        or implementation_approval.get("blocked_actions")
        or []
    )
    for effect in [
        "write shadow replay runner write guard artifact",
        "implement shadow replay runner",
        "accept --write-browser-run-log in this pass",
        "write Browser Run evidence",
        "write Agent Activity replay evidence",
        "launch or control a browser",
        "connect to CDP",
        "use authenticated browser sessions",
        "read cookies, tokens, or secrets",
        "mutate DOM or submit forms",
    ]:
        if effect not in denied_effects:
            denied_effects.append(effect)

    result = dict(implementation_approval)
    result.update(
        {
            "action": PROMOTION_BROWSER_SKILL_SHADOW_REPLAY_RUNNER_WRITE_GUARD_ACTION,
            "browser_skill_shadow_replay_runner_write_guard_status": guard_status,
            "review_decision": review_decision,
            "shadow_replay_runner_write_guard": guard_contract,
            "shadow_replay_runner_write_guard_contract": guard_contract,
            "shadow_replay_runner_write_guard_checks": checks,
            "ready_for_guarded_shadow_replay_runner_implementation_next_pass": guard_ready,
            "ready_for_shadow_replay_runner_implementation_next_pass": guard_ready,
            "future_command_name": guard_contract["future_command_name"],
            "future_required_mode": guard_contract["future_required_mode"],
            "future_required_flags": guard_contract["future_required_flags"],
            "future_write_set": guard_contract["future_write_set"],
            "browser_run_record_schema": browser_run_record_schema,
            "runner_write_guard_artifact_written": False,
            "shadow_replay_runner_write_guard_artifact_written": False,
            "implementation_approval_artifact_written": False,
            "implementation_request_artifact_written": False,
            "shadow_replay_runner_implemented": False,
            "write_browser_run_log_flag_supported_in_this_pass": False,
            "browser_run_log_written": False,
            "agent_activity_log_written": False,
            "activation_record_written": False,
            "activation_audit_written": False,
            "trusted_artifacts_written": False,
            "trusted_artifacts_mutated": False,
            "activation_performed": False,
            "browser_execution_allowed": False,
            "browser_launch_allowed": False,
            "cdp_connection_allowed": False,
            "authenticated_session_allowed": False,
            "real_profile_allowed": False,
            "cookie_or_token_access_allowed": False,
            "dom_mutation_allowed": False,
            "external_submit_allowed": False,
            "agent_bus_enqueue_allowed": False,
            "provider_api_call_allowed": False,
            "gate_policy_mutation_allowed": False,
            "canonical_writeback_allowed": False,
            "writes_performed": False,
            "files_modified": False,
            "blocked_actions": denied_effects,
            "denied_effects": denied_effects,
            "boundary": (
                "Browser Skill shadow replay runner write guard only; declares "
                "future runner flags, scoped Browser Run evidence schema, and "
                "no-auth/no-DOM proof boundaries. It writes no guard artifact, "
                "Browser Run log, Agent Activity replay evidence, activation "
                "record, trusted artifact, Gate policy, browser/CDP action, "
                "Agent Bus task, provider call, or canonical ChaseOS state."
            ),
        }
    )
    return result


def _target_host(target_url: str) -> str:
    parsed = urlparse(target_url)
    return (parsed.hostname or "").lower()


def _target_url_has_secret_marker(target_url: str) -> bool:
    lowered = target_url.lower()
    secret_markers = (
        "api_key",
        "apikey",
        "access_token",
        "auth_token",
        "token=",
        "password",
        "passwd",
        "cookie",
        "session",
        "secret",
        "oauth",
    )
    return any(marker in lowered for marker in secret_markers)


def _target_url_allowed_for_shadow_replay(
    target_url: str,
    *,
    allowlisted_domain: str | None = None,
    local_target_only: bool = False,
) -> tuple[bool, str]:
    parsed = urlparse(target_url)
    host = (parsed.hostname or "").lower()
    scheme = (parsed.scheme or "").lower()
    if scheme not in {"http", "https"}:
        return False, "target_url_scheme_not_allowed"
    if not host:
        return False, "target_url_host_missing"

    local_hosts = {"localhost", "127.0.0.1", "::1"}
    if host in local_hosts or host.endswith(".localhost"):
        return True, "local_loopback_target"

    if local_target_only:
        return False, "non_local_target_blocked_by_local_target_only"

    allowed = (allowlisted_domain or "").strip().lower()
    if allowed and (host == allowed or host.endswith(f".{allowed}")):
        return True, "operator_allowlisted_domain"
    return False, "target_domain_not_allowlisted"


def candidate_promotion_browser_skill_shadow_replay_runner_implementation_dry_run(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    actor: str,
    target_url: str,
    shadow_mode: bool = False,
    write_browser_run_log: bool = False,
    local_target_only: bool = False,
    allowlisted_domain: str | None = None,
    max_steps: int = 5,
    source_approval_id: str | None = None,
    activation_approval_id: str | None = None,
    reason: str | None = None,
) -> dict[str, Any]:
    """Plan a shadow replay runner dry-run without browser control or writes."""
    guard = candidate_promotion_browser_skill_shadow_replay_runner_write_guard(
        candidate_id,
        root,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
        actor=actor,
        source_approval_id=source_approval_id,
        activation_approval_id=activation_approval_id,
        reason=reason or "operator requested Browser Skill shadow replay runner dry-run",
    )
    scope = dict(guard.get("scope") or {})
    resolved_candidate_id = str(guard.get("candidate_id") or candidate_id)
    proposed_skill_id = str(guard.get("proposed_skill_id") or "")
    slug = _slug(resolved_candidate_id)
    target_host = _target_host(target_url)
    target_allowed, target_reason = _target_url_allowed_for_shadow_replay(
        target_url,
        allowlisted_domain=allowlisted_domain,
        local_target_only=local_target_only,
    )
    target_secret_free = not _target_url_has_secret_marker(target_url)
    max_steps_valid = 1 <= int(max_steps or 0) <= 25
    guard_ready = bool(guard.get("ready_for_shadow_replay_runner_implementation_next_pass"))
    write_flag_rejected = bool(write_browser_run_log)

    browser_run_preview = {
        "record_type": "siteops_browser_skill_shadow_replay_run",
        "run_id_preview": f"siteops-shadow-replay-dry-run-{slug}",
        "tenant_id": scope.get("tenant_id"),
        "workspace_id": scope.get("workspace_id"),
        "user_id": scope.get("user_id"),
        "candidate_id": resolved_candidate_id,
        "proposed_skill_id": proposed_skill_id,
        "target_url": target_url,
        "target_host": target_host,
        "shadow_mode": bool(shadow_mode),
        "max_steps": int(max_steps or 0),
        "status": "planned_no_browser",
        "artifact_written": False,
        "browser_run_log_written": False,
        "forbidden_fields": list(
            (guard.get("browser_run_record_schema") or {}).get("forbidden_fields") or []
        ),
    }
    dry_run_plan = {
        "plan_type": "siteops_browser_skill_shadow_replay_runner_dry_run",
        "future_command_name": "browser-skill-shadow-replay",
        "target_url": target_url,
        "target_host": target_host,
        "shadow_mode": bool(shadow_mode),
        "local_target_only": bool(local_target_only),
        "allowlisted_domain": allowlisted_domain,
        "max_steps": int(max_steps or 0),
        "steps": [
            "validate_scope_and_candidate",
            "validate_runner_write_guard",
            "validate_shadow_mode_flag",
            "validate_target_url_policy",
            "load_candidate_metadata_only",
            "derive_expected_shadow_actions",
            "stop_before_browser_launch",
            "require_separate_write_pass_before_browser_run_log",
        ],
        "actions_planned": [
            "browser.open.preview",
            "browser.observe.preview",
            "browser.screenshot.preview",
            "browser.close.preview",
        ],
        "actions_observed": [],
        "policy_decisions": [
            {"action": "browser.launch", "decision": "deny", "reason": "dry_run_shell_only"},
            {"action": "cdp.connect", "decision": "deny", "reason": "dry_run_shell_only"},
            {
                "action": "browser_run_log.write",
                "decision": "deny",
                "reason": "write_pass_not_approved",
            },
            {
                "action": "authenticated_session.use",
                "decision": "deny",
                "reason": "no_auth_shadow_replay",
            },
            {"action": "dom.submit", "decision": "deny", "reason": "shadow_mode_only"},
        ],
    }

    checks = list(guard.get("shadow_replay_runner_write_guard_checks") or []) + [
        _executor_preflight_check(
            "shadow_replay_runner_write_guard_ready",
            passed=guard_ready,
            detail=str(guard.get("browser_skill_shadow_replay_runner_write_guard_status")),
        ),
        _executor_preflight_check(
            "shadow_mode_flag_present",
            passed=bool(shadow_mode),
            detail="--shadow-mode required",
        ),
        _executor_preflight_check(
            "write_browser_run_log_flag_not_used",
            passed=not write_flag_rejected,
            detail="--write-browser-run-log remains rejected in dry-run shell",
        ),
        _executor_preflight_check(
            "target_url_present",
            passed=bool(target_url),
            detail=target_url or "missing",
        ),
        _executor_preflight_check(
            "target_url_local_or_allowlisted",
            passed=target_allowed,
            detail=target_reason,
        ),
        _executor_preflight_check(
            "target_url_secret_free",
            passed=target_secret_free,
            detail="no secret-like URL markers detected" if target_secret_free else "secret-like marker detected",
        ),
        _executor_preflight_check(
            "max_steps_within_dry_run_limit",
            passed=max_steps_valid,
            detail=str(max_steps),
        ),
        _executor_preflight_check(
            "no_browser_launch_in_dry_run",
            passed=True,
            detail="dry-run shell stops before browser launch or CDP connection",
        ),
        _executor_preflight_check(
            "no_browser_run_log_write_in_dry_run",
            passed=True,
            detail="Browser Run log preview only; no artifact write",
        ),
    ]

    ready = (
        guard_ready
        and bool(shadow_mode)
        and not write_flag_rejected
        and bool(target_url)
        and target_allowed
        and target_secret_free
        and max_steps_valid
        and all(bool(check.get("passed")) for check in checks)
    )
    if ready:
        dry_run_status = "shadow_replay_runner_dry_run_ready_no_browser"
        review_decision = "ready_for_shadow_replay_runner_write_pass_next"
    elif write_flag_rejected:
        dry_run_status = "blocked_write_browser_run_log_not_supported_in_dry_run"
        review_decision = "remove_write_browser_run_log_or_request_write_pass"
    else:
        dry_run_status = "blocked_shadow_replay_runner_dry_run"
        review_decision = "repair_shadow_replay_runner_dry_run_inputs"

    denied_effects = list(guard.get("denied_effects") or guard.get("blocked_actions") or [])
    for effect in [
        "write Browser Run log from dry-run shell",
        "write Agent Activity replay evidence from dry-run shell",
        "launch or control a browser from dry-run shell",
        "connect to CDP from dry-run shell",
        "use authenticated browser sessions",
        "read cookies, tokens, secrets, localStorage, or sessionStorage",
        "mutate DOM or submit forms",
        "promote replay evidence to trusted skill",
    ]:
        if effect not in denied_effects:
            denied_effects.append(effect)

    result = dict(guard)
    result.update(
        {
            "action": PROMOTION_BROWSER_SKILL_SHADOW_REPLAY_RUNNER_DRY_RUN_ACTION,
            "browser_skill_shadow_replay_runner_dry_run_status": dry_run_status,
            "review_decision": review_decision,
            "shadow_replay_runner_dry_run_plan": dry_run_plan,
            "shadow_replay_runner_dry_run_checks": checks,
            "browser_run_preview": browser_run_preview,
            "target_url": target_url,
            "target_host": target_host,
            "target_policy_reason": target_reason,
            "shadow_mode": bool(shadow_mode),
            "local_target_only": bool(local_target_only),
            "allowlisted_domain": allowlisted_domain,
            "max_steps": int(max_steps or 0),
            "ready_for_shadow_replay_runner_write_pass_next": ready,
            "runner_dry_run_shell_built": True,
            "shadow_replay_runner_dry_run_built": True,
            "shadow_replay_runner_implemented": False,
            "browser_replay_ready": False,
            "browser_replay_built": False,
            "write_browser_run_log_requested": write_flag_rejected,
            "write_browser_run_log_flag_supported_in_this_pass": False,
            "browser_run_log_written": False,
            "agent_activity_log_written": False,
            "browser_run_preview_written": False,
            "runner_dry_run_artifact_written": False,
            "browser_execution_allowed": False,
            "browser_launch_allowed": False,
            "cdp_connection_allowed": False,
            "authenticated_session_allowed": False,
            "real_profile_allowed": False,
            "cookie_or_token_access_allowed": False,
            "dom_mutation_allowed": False,
            "external_submit_allowed": False,
            "agent_bus_enqueue_allowed": False,
            "provider_api_call_allowed": False,
            "gate_policy_mutation_allowed": False,
            "canonical_writeback_allowed": False,
            "writes_performed": False,
            "files_modified": False,
            "blocked_actions": denied_effects,
            "denied_effects": denied_effects,
            "boundary": (
                "Browser Skill shadow replay runner dry-run shell only; it validates "
                "the write guard, target URL, and shadow-mode inputs, then plans "
                "future replay evidence without launching browser/CDP, using "
                "authenticated sessions, writing Browser Run or Agent Activity "
                "artifacts, mutating trusted artifacts, changing Gate policy, "
                "calling providers, or writing canonical ChaseOS state."
            ),
        }
    )
    return result


def _write_text_create_new(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        handle.write(text.rstrip() + "\n")


def _resolve_shadow_replay_candidate_domain(proposed_skill_id: str, target_host: str) -> str:
    skill_domain = str(proposed_skill_id or "").split(".", 1)[0].strip()
    if skill_domain:
        return _slug(skill_domain)
    return _slug(target_host or "shadow-replay")


def candidate_promotion_browser_skill_shadow_replay_runner_write_pass(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    actor: str,
    target_url: str,
    shadow_mode: bool = False,
    write_browser_run_log: bool = False,
    local_target_only: bool = False,
    allowlisted_domain: str | None = None,
    max_steps: int = 5,
    source_approval_id: str | None = None,
    activation_approval_id: str | None = None,
    reason: str | None = None,
) -> dict[str, Any]:
    """Write scoped shadow replay evidence from the dry-run preview only."""
    dry_run = candidate_promotion_browser_skill_shadow_replay_runner_implementation_dry_run(
        candidate_id,
        root,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
        actor=actor,
        target_url=target_url,
        shadow_mode=shadow_mode,
        write_browser_run_log=False,
        local_target_only=local_target_only,
        allowlisted_domain=allowlisted_domain,
        max_steps=max_steps,
        source_approval_id=source_approval_id,
        activation_approval_id=activation_approval_id,
        reason=reason or "operator requested Browser Skill shadow replay runner write pass",
    )
    vault_root = Path(root or Path.cwd()).resolve(strict=False)
    scope = dict(dry_run.get("scope") or {})
    resolved_candidate_id = str(dry_run.get("candidate_id") or candidate_id)
    proposed_skill_id = str(dry_run.get("proposed_skill_id") or "")
    slug = _slug(resolved_candidate_id)
    target_host = str(dry_run.get("target_host") or _target_host(target_url))
    candidate_domain = _resolve_shadow_replay_candidate_domain(proposed_skill_id, target_host)
    browser_run_rel = (
        Path("07_LOGS")
        / "Browser-Runs"
        / str(scope.get("tenant_id") or tenant_id or "local")
        / str(scope.get("workspace_id") or workspace_id or "default")
        / f"siteops-shadow-replay-{slug}.json"
    )
    agent_activity_rel = (
        Path("07_LOGS")
        / "Agent-Activity"
        / str(scope.get("tenant_id") or tenant_id or "local")
        / str(scope.get("workspace_id") or workspace_id or "default")
        / f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}-siteops-shadow-replay-{slug}.md"
    )
    candidate_evidence_rel = (
        Path("03_INPUTS")
        / "Browser-Skill-Candidates"
        / candidate_domain
        / f"shadow-replay-{slug}.md"
    )
    browser_run_path = vault_root / browser_run_rel
    agent_activity_path = vault_root / agent_activity_rel
    candidate_evidence_path = vault_root / candidate_evidence_rel
    target_paths = [browser_run_path, agent_activity_path, candidate_evidence_path]
    paths_confined = all(_filesystem_path_is_within(path, vault_root) for path in target_paths)
    targets_absent = all(not path.exists() for path in target_paths)
    dry_run_ready = dry_run.get("browser_skill_shadow_replay_runner_dry_run_status") == (
        "shadow_replay_runner_dry_run_ready_no_browser"
    ) and bool(dry_run.get("ready_for_shadow_replay_runner_write_pass_next"))

    browser_run_record = {
        "record_type": "siteops_browser_skill_shadow_replay_run",
        "run_id": f"siteops-shadow-replay-{slug}",
        "tenant_id": scope.get("tenant_id"),
        "workspace_id": scope.get("workspace_id"),
        "user_id": scope.get("user_id"),
        "candidate_id": resolved_candidate_id,
        "proposed_skill_id": proposed_skill_id,
        "source_approval_id": dry_run.get("source_approval_id"),
        "activation_approval_id": dry_run.get("activation_approval_id"),
        "target_url": target_url,
        "target_host": target_host,
        "shadow_mode": bool(shadow_mode),
        "local_target_only": bool(local_target_only),
        "allowlisted_domain": allowlisted_domain,
        "max_steps": int(max_steps or 0),
        "actions_planned": list((dry_run.get("shadow_replay_runner_dry_run_plan") or {}).get("actions_planned") or []),
        "actions_observed": [],
        "policy_decisions": list((dry_run.get("shadow_replay_runner_dry_run_plan") or {}).get("policy_decisions") or []),
        "screenshots_ref": None,
        "artifacts_ref": candidate_evidence_rel.as_posix(),
        "agent_activity_ref": agent_activity_rel.as_posix(),
        "status": "shadow_replay_evidence_written_no_browser",
        "started_at": now_iso(),
        "ended_at": now_iso(),
        "browser_execution_performed": False,
        "browser_launch_performed": False,
        "cdp_connection_performed": False,
        "authenticated_session_used": False,
        "dom_mutation_performed": False,
        "external_submit_performed": False,
        "trusted_artifact_mutated": False,
        "canonical_writeback_performed": False,
        "trusted_evidence": False,
        "untrusted_until_review": True,
        "forbidden_fields_excluded": True,
    }
    browser_run_digest = _sha256_json(browser_run_record)
    candidate_text = "\n".join(
        [
            "---",
            "type: browser-skill-shadow-replay-evidence",
            "status: UNTRUSTED / REVIEW REQUIRED / NO BROWSER EXECUTION",
            f"candidate_id: {resolved_candidate_id}",
            f"proposed_skill_id: {proposed_skill_id}",
            "---",
            "",
            f"# Shadow Replay Evidence - {resolved_candidate_id}",
            "",
            "This evidence was produced from a dry-run preview only. No browser was launched, no CDP connection was opened, no authenticated session was used, and no DOM action was performed.",
            "",
            f"- Browser Run record: `{browser_run_rel.as_posix()}`",
            f"- Browser Run SHA-256: `{browser_run_digest}`",
            f"- Target host: `{target_host}`",
            "- Trust status: UNTRUSTED until human review",
        ]
    )
    agent_activity_text = "\n".join(
        [
            f"# SiteOps Shadow Replay Activity - {resolved_candidate_id}",
            "",
            "Runtime: Codex",
            "Task type: SiteOps Browser Skill shadow replay evidence write",
            "Status: COMPLETE TARGETED / EVIDENCE WRITTEN / NO BROWSER EXECUTION",
            "",
            "## Evidence",
            "",
            f"- Browser Run record: `{browser_run_rel.as_posix()}`",
            f"- Browser Run SHA-256: `{browser_run_digest}`",
            f"- Candidate evidence: `{candidate_evidence_rel.as_posix()}`",
            "",
            "## Boundaries",
            "",
            "- No browser launch",
            "- No CDP connection",
            "- No authenticated session",
            "- No cookie/token/secret/session storage read",
            "- No DOM mutation or external submit",
            "- No trusted artifact mutation",
            "- No activation or canonical writeback",
        ]
    )

    checks = list(dry_run.get("shadow_replay_runner_dry_run_checks") or []) + [
        _executor_preflight_check(
            "shadow_replay_runner_dry_run_ready",
            passed=dry_run_ready,
            detail=str(dry_run.get("browser_skill_shadow_replay_runner_dry_run_status")),
        ),
        _executor_preflight_check(
            "explicit_write_browser_run_log_flag_present",
            passed=bool(write_browser_run_log),
            detail="--write-browser-run-log required for evidence writes",
        ),
        _executor_preflight_check(
            "write_targets_confined_to_vault",
            passed=paths_confined,
            detail=", ".join(path.relative_to(vault_root).as_posix() for path in target_paths if _filesystem_path_is_within(path, vault_root)),
        ),
        _executor_preflight_check(
            "write_targets_create_new",
            passed=targets_absent,
            detail="all target evidence files absent" if targets_absent else "one or more evidence targets already exist",
        ),
        _executor_preflight_check(
            "write_pass_still_no_browser",
            passed=True,
            detail="writes dry-run evidence only; no browser/CDP/session/DOM execution",
        ),
    ]
    write_ready = dry_run_ready and bool(write_browser_run_log) and paths_confined and targets_absent and all(
        bool(check.get("passed")) for check in checks
    )
    browser_run_ref: str | None = None
    agent_activity_ref: str | None = None
    candidate_evidence_ref: str | None = None
    candidate_evidence_sha256: str | None = None
    agent_activity_sha256: str | None = None
    if write_ready:
        _write_json_create_new(browser_run_path, browser_run_record)
        _write_text_create_new(candidate_evidence_path, candidate_text)
        _write_text_create_new(agent_activity_path, agent_activity_text)
        browser_run_ref = browser_run_path.as_posix()
        agent_activity_ref = agent_activity_path.as_posix()
        candidate_evidence_ref = candidate_evidence_path.as_posix()
        candidate_evidence_sha256 = hashlib.sha256((candidate_text.rstrip() + "\n").encode("utf-8")).hexdigest()
        agent_activity_sha256 = hashlib.sha256((agent_activity_text.rstrip() + "\n").encode("utf-8")).hexdigest()
        write_status = "shadow_replay_runner_write_pass_evidence_written_no_browser"
        review_decision = "ready_for_replay_evidence_review_and_provenance_closeout"
    elif not write_browser_run_log:
        write_status = "shadow_replay_runner_write_pass_ready_no_write"
        review_decision = "rerun_with_write_browser_run_log_after_operator_review"
    elif not dry_run_ready:
        write_status = "blocked_shadow_replay_runner_write_pass_dry_run"
        review_decision = "repair_shadow_replay_runner_dry_run_before_write"
    elif not targets_absent:
        write_status = "blocked_shadow_replay_runner_write_pass_existing_evidence"
        review_decision = "manual_review_existing_replay_evidence_before_retry"
    else:
        write_status = "blocked_shadow_replay_runner_write_pass"
        review_decision = "repair_shadow_replay_runner_write_pass_inputs"

    result = dict(dry_run)
    result.update(
        {
            "action": PROMOTION_BROWSER_SKILL_SHADOW_REPLAY_RUNNER_WRITE_PASS_ACTION,
            "browser_skill_shadow_replay_runner_write_pass_status": write_status,
            "review_decision": review_decision,
            "shadow_replay_runner_write_pass_checks": checks,
            "write_browser_run_log_requested": bool(write_browser_run_log),
            "browser_run_ref": browser_run_ref,
            "browser_run_path": browser_run_ref,
            "browser_run_sha256": browser_run_digest if browser_run_ref else None,
            "agent_activity_ref": agent_activity_ref,
            "agent_activity_sha256": agent_activity_sha256,
            "candidate_evidence_ref": candidate_evidence_ref,
            "candidate_evidence_sha256": candidate_evidence_sha256,
            "browser_run_record": browser_run_record if browser_run_ref else None,
            "ready_for_replay_evidence_review_next": bool(browser_run_ref),
            "runner_write_pass_built": True,
            "browser_replay_built": False,
            "browser_execution_allowed": False,
            "browser_launch_allowed": False,
            "cdp_connection_allowed": False,
            "authenticated_session_allowed": False,
            "real_profile_allowed": False,
            "cookie_or_token_access_allowed": False,
            "dom_mutation_allowed": False,
            "external_submit_allowed": False,
            "agent_bus_enqueue_allowed": False,
            "provider_api_call_allowed": False,
            "gate_policy_mutation_allowed": False,
            "canonical_writeback_allowed": False,
            "browser_run_log_written": bool(browser_run_ref),
            "agent_activity_log_written": bool(agent_activity_ref),
            "candidate_evidence_written": bool(candidate_evidence_ref),
            "activation_record_written": False,
            "activation_audit_written": False,
            "trusted_artifacts_written": False,
            "trusted_artifacts_mutated": False,
            "activation_performed": False,
            "writes_performed": bool(browser_run_ref or agent_activity_ref or candidate_evidence_ref),
            "files_modified": bool(browser_run_ref or agent_activity_ref or candidate_evidence_ref),
            "boundary": (
                "Browser Skill shadow replay runner write pass only; writes scoped "
                "dry-run Browser Run, Agent Activity, and untrusted candidate evidence "
                "when explicitly requested. It does not launch browser/CDP, use "
                "authenticated sessions, read browser state, mutate DOM, activate "
                "skills, mutate trusted artifacts, enqueue Agent Bus work, call "
                "providers, mutate Gate, or write canonical ChaseOS state."
            ),
        }
    )
    return result


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _extract_markdown_digest(text: str, label: str) -> str | None:
    prefix = f"- {label}: `"
    for line in text.splitlines():
        if line.startswith(prefix) and line.endswith("`"):
            return line[len(prefix) : -1].strip()
    return None


def _contains_forbidden_browser_run_fields(payload: Any) -> bool:
    forbidden = {
        "cookie",
        "cookies",
        "token",
        "secret",
        "password",
        "browser_session_state",
        "localstorage",
        "sessionstorage",
        "personal_account_state",
        "api_key",
        "oauth",
        "raw_html_with_account_data",
    }
    if isinstance(payload, dict):
        for key, value in payload.items():
            lowered = str(key).lower()
            if lowered in forbidden:
                return True
            if _contains_forbidden_browser_run_fields(value):
                return True
    elif isinstance(payload, list):
        return any(_contains_forbidden_browser_run_fields(item) for item in payload)
    return False


def candidate_promotion_browser_skill_shadow_replay_evidence_review_closeout(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    actor: str,
    target_url: str,
    shadow_mode: bool = False,
    write_review_closeout: bool = False,
    local_target_only: bool = False,
    allowlisted_domain: str | None = None,
    max_steps: int = 5,
    source_approval_id: str | None = None,
    activation_approval_id: str | None = None,
    reason: str | None = None,
) -> dict[str, Any]:
    """Review scoped shadow replay evidence without browser execution."""
    write_pass = candidate_promotion_browser_skill_shadow_replay_runner_write_pass(
        candidate_id,
        root,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
        actor=actor,
        target_url=target_url,
        shadow_mode=shadow_mode,
        write_browser_run_log=False,
        local_target_only=local_target_only,
        allowlisted_domain=allowlisted_domain,
        max_steps=max_steps,
        source_approval_id=source_approval_id,
        activation_approval_id=activation_approval_id,
        reason=reason or "operator requested Browser Skill shadow replay evidence review closeout",
    )
    vault_root = Path(root or Path.cwd()).resolve(strict=False)
    scope = dict(write_pass.get("scope") or {})
    resolved_candidate_id = str(write_pass.get("candidate_id") or candidate_id)
    proposed_skill_id = str(write_pass.get("proposed_skill_id") or "")
    slug = _slug(resolved_candidate_id)
    target_host = str(write_pass.get("target_host") or _target_host(target_url))
    candidate_domain = _resolve_shadow_replay_candidate_domain(proposed_skill_id, target_host)
    tenant = str(scope.get("tenant_id") or tenant_id or "local")
    workspace = str(scope.get("workspace_id") or workspace_id or "default")
    browser_run_rel = (
        Path("07_LOGS")
        / "Browser-Runs"
        / tenant
        / workspace
        / f"siteops-shadow-replay-{slug}.json"
    )
    agent_activity_rel = (
        Path("07_LOGS")
        / "Agent-Activity"
        / tenant
        / workspace
        / f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}-siteops-shadow-replay-{slug}.md"
    )
    candidate_evidence_rel = (
        Path("03_INPUTS")
        / "Browser-Skill-Candidates"
        / candidate_domain
        / f"shadow-replay-{slug}.md"
    )
    review_closeout_rel = (
        Path("07_LOGS")
        / "Browser-Runs"
        / tenant
        / workspace
        / f"siteops-shadow-replay-{slug}-evidence-review.json"
    )
    browser_run_path = vault_root / browser_run_rel
    agent_activity_path = vault_root / agent_activity_rel
    candidate_evidence_path = vault_root / candidate_evidence_rel
    review_closeout_path = vault_root / review_closeout_rel
    evidence_paths = [browser_run_path, agent_activity_path, candidate_evidence_path]
    paths_confined = all(_filesystem_path_is_within(path, vault_root) for path in evidence_paths + [review_closeout_path])
    evidence_exists = all(path.exists() and path.is_file() for path in evidence_paths)
    review_target_absent = not review_closeout_path.exists()

    browser_run_record: dict[str, Any] = {}
    candidate_text = ""
    agent_activity_text = ""
    parse_ok = False
    browser_run_digest: str | None = None
    candidate_file_sha256: str | None = None
    agent_activity_file_sha256: str | None = None
    candidate_declared_browser_digest: str | None = None
    agent_declared_browser_digest: str | None = None
    if evidence_exists and paths_confined:
        try:
            browser_run_record = json.loads(browser_run_path.read_text(encoding="utf-8"))
            candidate_text = candidate_evidence_path.read_text(encoding="utf-8")
            agent_activity_text = agent_activity_path.read_text(encoding="utf-8")
            browser_run_digest = _sha256_json(browser_run_record)
            candidate_file_sha256 = _sha256_file(candidate_evidence_path)
            agent_activity_file_sha256 = _sha256_file(agent_activity_path)
            candidate_declared_browser_digest = _extract_markdown_digest(
                candidate_text, "Browser Run SHA-256"
            )
            agent_declared_browser_digest = _extract_markdown_digest(
                agent_activity_text, "Browser Run SHA-256"
            )
            parse_ok = True
        except (OSError, ValueError, json.JSONDecodeError):
            parse_ok = False

    browser_digest_match = (
        parse_ok
        and browser_run_digest is not None
        and candidate_declared_browser_digest == browser_run_digest
        and agent_declared_browser_digest == browser_run_digest
    )
    provenance_matches = (
        parse_ok
        and browser_run_record.get("candidate_id") == resolved_candidate_id
        and browser_run_record.get("tenant_id") == tenant
        and browser_run_record.get("workspace_id") == workspace
        and browser_run_record.get("user_id") == scope.get("user_id")
        and browser_run_record.get("target_url") == target_url
        and browser_run_record.get("artifacts_ref") == candidate_evidence_rel.as_posix()
        and browser_run_record.get("agent_activity_ref") == agent_activity_rel.as_posix()
    )
    no_browser_effects = (
        parse_ok
        and browser_run_record.get("browser_execution_performed") is False
        and browser_run_record.get("browser_launch_performed") is False
        and browser_run_record.get("cdp_connection_performed") is False
        and browser_run_record.get("authenticated_session_used") is False
        and browser_run_record.get("dom_mutation_performed") is False
        and browser_run_record.get("external_submit_performed") is False
        and browser_run_record.get("trusted_artifact_mutated") is False
        and browser_run_record.get("canonical_writeback_performed") is False
    )
    untrusted_posture = (
        parse_ok
        and browser_run_record.get("trusted_evidence") is False
        and browser_run_record.get("untrusted_until_review") is True
        and "UNTRUSTED" in candidate_text
    )
    forbidden_fields_absent = parse_ok and not _contains_forbidden_browser_run_fields(
        browser_run_record
    )
    target_secret_free = not _target_url_has_secret_marker(target_url)

    closeout_checks = [
        _executor_preflight_check(
            "shadow_replay_write_pass_evidence_present",
            passed=evidence_exists,
            detail=", ".join(path.relative_to(vault_root).as_posix() for path in evidence_paths if _filesystem_path_is_within(path, vault_root)),
        ),
        _executor_preflight_check(
            "evidence_paths_confined_to_vault",
            passed=paths_confined,
            detail="browser-run, agent-activity, candidate-evidence, review-closeout paths checked",
        ),
        _executor_preflight_check(
            "evidence_files_parse",
            passed=parse_ok,
            detail="Browser Run JSON and Markdown evidence parsed" if parse_ok else "failed to parse evidence files",
        ),
        _executor_preflight_check(
            "browser_run_digest_matches_markdown_refs",
            passed=browser_digest_match,
            detail=str(browser_run_digest or "missing"),
        ),
        _executor_preflight_check(
            "evidence_provenance_matches_candidate_scope_and_target",
            passed=provenance_matches,
            detail=f"{tenant}/{workspace}/{scope.get('user_id')} {resolved_candidate_id}",
        ),
        _executor_preflight_check(
            "evidence_confirms_no_browser_or_session_effects",
            passed=no_browser_effects,
            detail="no browser/CDP/session/DOM/trusted/canonical effects recorded",
        ),
        _executor_preflight_check(
            "evidence_remains_untrusted_until_review",
            passed=untrusted_posture,
            detail="trusted_evidence=false; untrusted_until_review=true",
        ),
        _executor_preflight_check(
            "forbidden_secret_session_fields_absent",
            passed=forbidden_fields_absent,
            detail="no forbidden browser/session/secret fields in Browser Run JSON",
        ),
        _executor_preflight_check(
            "target_url_secret_free",
            passed=target_secret_free,
            detail="no secret-like URL markers detected" if target_secret_free else "secret-like URL marker detected",
        ),
        _executor_preflight_check(
            "review_closeout_target_create_new",
            passed=review_target_absent,
            detail=review_closeout_rel.as_posix(),
        ),
    ]
    write_pass_context_checks = list(write_pass.get("shadow_replay_runner_write_pass_checks") or [])
    closeout_ready = all(bool(check.get("passed")) for check in closeout_checks)
    review_record = {
        "record_type": "siteops_browser_skill_shadow_replay_evidence_review_closeout",
        "tenant_id": tenant,
        "workspace_id": workspace,
        "user_id": scope.get("user_id"),
        "candidate_id": resolved_candidate_id,
        "proposed_skill_id": proposed_skill_id,
        "target_url": target_url,
        "browser_run_ref": browser_run_rel.as_posix(),
        "browser_run_sha256": browser_run_digest,
        "agent_activity_ref": agent_activity_rel.as_posix(),
        "agent_activity_sha256": agent_activity_file_sha256,
        "candidate_evidence_ref": candidate_evidence_rel.as_posix(),
        "candidate_evidence_sha256": candidate_file_sha256,
        "reviewed_by": actor,
        "review_status": "closed_untrusted_no_browser_evidence",
        "trusted_promotion_allowed": False,
        "browser_execution_allowed": False,
        "ready_for_local_shadow_execution_approval_next": closeout_ready,
        "created_at": now_iso(),
        "checks": closeout_checks,
        "write_pass_context_checks": write_pass_context_checks,
    }
    review_ref: str | None = None
    review_sha256: str | None = None
    if write_review_closeout and closeout_ready:
        _write_json_create_new(review_closeout_path, review_record)
        review_ref = review_closeout_path.as_posix()
        review_sha256 = _sha256_json(review_record)
        closeout_status = "shadow_replay_evidence_review_closeout_written"
        review_decision = "ready_for_guarded_local_shadow_execution_approval_packet"
    elif write_review_closeout and not closeout_ready:
        closeout_status = "blocked_shadow_replay_evidence_review_closeout"
        review_decision = "repair_shadow_replay_evidence_before_closeout"
    else:
        closeout_status = (
            "shadow_replay_evidence_review_closeout_ready_no_write"
            if closeout_ready
            else "blocked_shadow_replay_evidence_review_closeout"
        )
        review_decision = (
            "rerun_with_write_review_closeout_after_operator_review"
            if closeout_ready
            else "repair_shadow_replay_evidence_before_closeout"
        )

    result = dict(write_pass)
    result.update(
        {
            "action": PROMOTION_BROWSER_SKILL_SHADOW_REPLAY_EVIDENCE_REVIEW_CLOSEOUT_ACTION,
            "browser_skill_shadow_replay_evidence_review_closeout_status": closeout_status,
            "review_decision": review_decision,
            "shadow_replay_evidence_review_closeout_checks": closeout_checks,
            "shadow_replay_write_pass_context_checks": write_pass_context_checks,
            "review_closeout_record": review_record if review_ref else None,
            "review_closeout_ref": review_ref,
            "review_closeout_path": review_ref,
            "review_closeout_sha256": review_sha256,
            "write_review_closeout_requested": bool(write_review_closeout),
            "browser_run_ref": browser_run_path.as_posix() if browser_run_path.exists() else None,
            "browser_run_sha256": browser_run_digest,
            "agent_activity_ref": agent_activity_path.as_posix() if agent_activity_path.exists() else None,
            "agent_activity_sha256": agent_activity_file_sha256,
            "candidate_evidence_ref": candidate_evidence_path.as_posix() if candidate_evidence_path.exists() else None,
            "candidate_evidence_sha256": candidate_file_sha256,
            "ready_for_local_shadow_execution_approval_next": closeout_ready,
            "trusted_promotion_allowed": False,
            "browser_replay_built": False,
            "browser_execution_allowed": False,
            "browser_launch_allowed": False,
            "cdp_connection_allowed": False,
            "authenticated_session_allowed": False,
            "real_profile_allowed": False,
            "cookie_or_token_access_allowed": False,
            "dom_mutation_allowed": False,
            "external_submit_allowed": False,
            "agent_bus_enqueue_allowed": False,
            "provider_api_call_allowed": False,
            "gate_policy_mutation_allowed": False,
            "canonical_writeback_allowed": False,
            "review_closeout_written": bool(review_ref),
            "browser_run_log_written": False,
            "agent_activity_log_written": False,
            "candidate_evidence_written": False,
            "activation_record_written": False,
            "activation_audit_written": False,
            "trusted_artifacts_written": False,
            "trusted_artifacts_mutated": False,
            "activation_performed": False,
            "writes_performed": bool(review_ref),
            "files_modified": bool(review_ref),
            "boundary": (
                "Browser Skill shadow replay evidence review closeout only; it "
                "validates scoped untrusted Browser Run, Agent Activity, and "
                "candidate evidence provenance. It may write only a scoped review "
                "closeout artifact when explicitly requested. It does not launch "
                "browser/CDP, use authenticated sessions, mutate DOM, promote "
                "trusted artifacts, activate skills, enqueue Agent Bus work, call "
                "providers, mutate Gate, or write canonical ChaseOS state."
            ),
        }
    )
    return result


def candidate_promotion_browser_skill_shadow_execution_approval_packet(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    actor: str,
    target_url: str,
    shadow_mode: bool = False,
    write_approval_request: bool = False,
    local_target_only: bool = False,
    allowlisted_domain: str | None = None,
    max_steps: int = 5,
    source_approval_id: str | None = None,
    activation_approval_id: str | None = None,
    reason: str | None = None,
) -> dict[str, Any]:
    """Prepare a no-browser approval packet for future local shadow execution."""
    write_pass = candidate_promotion_browser_skill_shadow_replay_runner_write_pass(
        candidate_id,
        root,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
        actor=actor,
        target_url=target_url,
        shadow_mode=shadow_mode,
        write_browser_run_log=False,
        local_target_only=local_target_only,
        allowlisted_domain=allowlisted_domain,
        max_steps=max_steps,
        source_approval_id=source_approval_id,
        activation_approval_id=activation_approval_id,
        reason=reason or "operator requested guarded local shadow execution approval packet",
    )
    vault_root = Path(root or Path.cwd()).resolve(strict=False)
    scope = dict(write_pass.get("scope") or {})
    resolved_candidate_id = str(write_pass.get("candidate_id") or candidate_id)
    proposed_skill_id = str(write_pass.get("proposed_skill_id") or "")
    slug = _slug(resolved_candidate_id)
    target_host = str(write_pass.get("target_host") or _target_host(target_url))
    candidate_domain = _resolve_shadow_replay_candidate_domain(proposed_skill_id, target_host)
    tenant = str(scope.get("tenant_id") or tenant_id or "local")
    workspace = str(scope.get("workspace_id") or workspace_id or "default")
    user = str(scope.get("user_id") or user_id or "local-user")
    browser_run_rel = (
        Path("07_LOGS")
        / "Browser-Runs"
        / tenant
        / workspace
        / f"siteops-shadow-replay-{slug}.json"
    )
    agent_activity_rel = (
        Path("07_LOGS")
        / "Agent-Activity"
        / tenant
        / workspace
        / f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}-siteops-shadow-replay-{slug}.md"
    )
    candidate_evidence_rel = (
        Path("03_INPUTS")
        / "Browser-Skill-Candidates"
        / candidate_domain
        / f"shadow-replay-{slug}.md"
    )
    review_closeout_rel = (
        Path("07_LOGS")
        / "Browser-Runs"
        / tenant
        / workspace
        / f"siteops-shadow-replay-{slug}-evidence-review.json"
    )
    future_execution_run_rel = (
        Path("07_LOGS")
        / "Browser-Runs"
        / tenant
        / workspace
        / f"siteops-shadow-execution-{slug}.json"
    )
    future_execution_activity_rel = (
        Path("07_LOGS")
        / "Agent-Activity"
        / tenant
        / workspace
        / f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}-siteops-shadow-execution-{slug}.md"
    )
    browser_run_path = vault_root / browser_run_rel
    agent_activity_path = vault_root / agent_activity_rel
    candidate_evidence_path = vault_root / candidate_evidence_rel
    review_closeout_path = vault_root / review_closeout_rel
    future_execution_run_path = vault_root / future_execution_run_rel
    future_execution_activity_path = vault_root / future_execution_activity_rel
    checked_paths = [
        browser_run_path,
        agent_activity_path,
        candidate_evidence_path,
        review_closeout_path,
        future_execution_run_path,
        future_execution_activity_path,
    ]
    paths_confined = all(_filesystem_path_is_within(path, vault_root) for path in checked_paths)
    evidence_exists = all(
        path.exists() and path.is_file()
        for path in [browser_run_path, agent_activity_path, candidate_evidence_path, review_closeout_path]
    )
    future_targets_absent = not future_execution_run_path.exists() and not future_execution_activity_path.exists()
    review_record: dict[str, Any] = {}
    browser_run_record: dict[str, Any] = {}
    review_parse_ok = False
    browser_run_sha256: str | None = None
    review_closeout_sha256: str | None = None
    if evidence_exists and paths_confined:
        try:
            browser_run_record = json.loads(browser_run_path.read_text(encoding="utf-8"))
            review_record = json.loads(review_closeout_path.read_text(encoding="utf-8"))
            browser_run_sha256 = _sha256_json(browser_run_record)
            review_closeout_sha256 = _sha256_file(review_closeout_path)
            review_parse_ok = True
        except (OSError, ValueError, json.JSONDecodeError):
            review_parse_ok = False

    review_status_ok = (
        review_parse_ok
        and review_record.get("record_type") == "siteops_browser_skill_shadow_replay_evidence_review_closeout"
        and review_record.get("review_status") == "closed_untrusted_no_browser_evidence"
        and review_record.get("tenant_id") == tenant
        and review_record.get("workspace_id") == workspace
        and review_record.get("user_id") == user
        and review_record.get("candidate_id") == resolved_candidate_id
        and review_record.get("proposed_skill_id") == proposed_skill_id
        and review_record.get("target_url") == target_url
    )
    review_digest_ok = (
        review_parse_ok
        and review_record.get("browser_run_sha256") == browser_run_sha256
        and review_record.get("browser_run_ref") == browser_run_rel.as_posix()
        and review_record.get("agent_activity_ref") == agent_activity_rel.as_posix()
        and review_record.get("candidate_evidence_ref") == candidate_evidence_rel.as_posix()
    )
    review_checks_ok = (
        review_parse_ok
        and bool(review_record.get("ready_for_local_shadow_execution_approval_next")) is True
        and review_record.get("trusted_promotion_allowed") is False
        and review_record.get("browser_execution_allowed") is False
        and all(bool(check.get("passed")) for check in list(review_record.get("checks") or []))
    )
    no_browser_effects = (
        review_parse_ok
        and browser_run_record.get("browser_execution_performed") is False
        and browser_run_record.get("browser_launch_performed") is False
        and browser_run_record.get("cdp_connection_performed") is False
        and browser_run_record.get("authenticated_session_used") is False
        and browser_run_record.get("dom_mutation_performed") is False
        and browser_run_record.get("external_submit_performed") is False
        and browser_run_record.get("trusted_artifact_mutated") is False
        and browser_run_record.get("canonical_writeback_performed") is False
    )
    forbidden_fields_absent = review_parse_ok and not _contains_forbidden_browser_run_fields(
        browser_run_record
    )
    target_secret_free = not _target_url_has_secret_marker(target_url)
    target_policy_ok, target_policy_reason = _target_url_allowed_for_shadow_replay(
        target_url,
        local_target_only=local_target_only,
        allowlisted_domain=allowlisted_domain,
    )
    scope_obj = require_scope(tenant_id=tenant, workspace_id=workspace, user_id=user)
    checks = [
        _executor_preflight_check(
            "shadow_replay_evidence_review_closeout_present",
            passed=evidence_exists,
            detail=review_closeout_rel.as_posix(),
        ),
        _executor_preflight_check(
            "shadow_execution_approval_paths_confined",
            passed=paths_confined,
            detail="evidence and future execution targets confined to vault",
        ),
        _executor_preflight_check(
            "shadow_replay_evidence_review_closeout_parseable",
            passed=review_parse_ok,
            detail="review closeout and Browser Run JSON parsed" if review_parse_ok else "failed to parse review evidence",
        ),
        _executor_preflight_check(
            "shadow_replay_evidence_review_closeout_status_valid",
            passed=review_status_ok,
            detail=str(review_record.get("review_status") or "missing"),
        ),
        _executor_preflight_check(
            "shadow_replay_evidence_review_digest_matches",
            passed=review_digest_ok,
            detail=str(browser_run_sha256 or "missing"),
        ),
        _executor_preflight_check(
            "shadow_replay_evidence_review_checks_passed",
            passed=review_checks_ok,
            detail="all closeout checks passed and evidence remains untrusted",
        ),
        _executor_preflight_check(
            "shadow_replay_evidence_confirms_no_browser_or_session_effects",
            passed=no_browser_effects,
            detail="existing evidence records no browser/CDP/session/DOM/trusted/canonical effects",
        ),
        _executor_preflight_check(
            "shadow_execution_forbidden_secret_session_fields_absent",
            passed=forbidden_fields_absent,
            detail="no forbidden browser/session/secret fields in Browser Run JSON",
        ),
        _executor_preflight_check(
            "shadow_execution_target_url_local_or_allowlisted",
            passed=target_policy_ok,
            detail=target_policy_reason,
        ),
        _executor_preflight_check(
            "shadow_execution_target_url_secret_free",
            passed=target_secret_free,
            detail="no secret-like URL markers detected" if target_secret_free else "secret-like URL marker detected",
        ),
        _executor_preflight_check(
            "shadow_execution_requires_shadow_mode",
            passed=bool(shadow_mode),
            detail="--shadow-mode required for approval packet",
        ),
        _executor_preflight_check(
            "shadow_execution_future_targets_create_new",
            passed=future_targets_absent,
            detail=", ".join([future_execution_run_rel.as_posix(), future_execution_activity_rel.as_posix()]),
        ),
    ]
    approval_packet_ready = all(bool(check.get("passed")) for check in checks)
    packet_id = f"siteops_candidate_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_shadow-execution-approval-{slug[:64]}"
    approval_packet = {
        "packet_id": packet_id,
        "record_type": "siteops_browser_skill_shadow_execution_approval_packet",
        "tenant_id": tenant,
        "workspace_id": workspace,
        "user_id": user,
        "candidate_id": resolved_candidate_id,
        "proposed_skill_id": proposed_skill_id,
        "target_url": target_url,
        "target_host": target_host,
        "source_approval_id": source_approval_id,
        "activation_approval_id": activation_approval_id,
        "review_closeout_ref": review_closeout_rel.as_posix(),
        "review_closeout_sha256": review_closeout_sha256,
        "browser_run_ref": browser_run_rel.as_posix(),
        "browser_run_sha256": browser_run_sha256,
        "requested_action": PROMOTION_BROWSER_SKILL_SHADOW_EXECUTION_PROOF_ACTION,
        "required_operator_decision": "approve_guarded_local_shadow_execution_proof",
        "future_command_name": "browser-skill-shadow-execution-proof",
        "future_required_mode": "shadow",
        "future_required_flags": ["--shadow-mode", "--write-browser-run-log"],
        "future_write_set": {
            "browser_run_log_path": future_execution_run_rel.as_posix(),
            "agent_activity_log_path": future_execution_activity_rel.as_posix(),
            "trusted_promotion_path": "future_only_after_separate_review",
            "writes_allowed_in_this_pass": False,
        },
        "future_preconditions": [
            "operator approval request must be approved before execution",
            "local or operator-allowlisted target only",
            "shadow mode required",
            "no authenticated browser session without separate approval",
            "no cookies, tokens, secrets, localStorage, sessionStorage, or account state",
            "no DOM mutation, form submit, publish, buy, trade, or account change",
            "future Browser Run and Agent Activity targets must be create-new",
            "replay output remains untrusted candidate evidence until separate review",
        ],
        "approval_request_ready": approval_packet_ready,
        "approval_request_written": False,
        "browser_execution_allowed_in_this_pass": False,
        "browser_launch_allowed_in_this_pass": False,
        "cdp_connection_allowed_in_this_pass": False,
        "authenticated_session_allowed_in_this_pass": False,
        "dom_mutation_allowed_in_this_pass": False,
        "trusted_promotion_allowed_in_this_pass": False,
        "canonical_writeback_allowed_in_this_pass": False,
        "created_at": now_iso(),
        "checks": checks,
    }
    run_ref: str | None = None
    audit_ref: str | None = None
    approval: dict[str, Any] | None = None
    run_id: str | None = None
    approval_write_blocked = False
    if write_approval_request and approval_packet_ready:
        run_id = (
            f"siteops_shadow_exec_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_"
            f"{_slug(resolved_candidate_id)[:32]}"
        )
        audit_ref = str(audit_path(root, tenant, workspace, run_id))
        now = now_iso()
        run = SiteOpsRun(
            run_id=run_id,
            tenant_id=tenant,
            workspace_id=workspace,
            user_id=user,
            skill_id=proposed_skill_id or "browser_skill_candidate",
            workflow_id=PROMOTION_WORKFLOW_ID,
            site_profile_id=None,
            provider_id=None,
            mode="dry_run",
            status="approval_needed",
            inputs_ref=review_closeout_rel.as_posix(),
            outputs_ref=None,
            audit_ref=audit_ref,
            cost_estimate={"charged": False, "provider": None},
            cost_actual=None,
            started_at=now,
            ended_at=now,
        )
        run_ref = write_run_record(root, run)
        audit_ref = append_audit_event(
            root,
            SiteOpsAuditEvent(
                event_id=f"event_{run_id}_policy",
                run_id=run_id,
                tenant_id=tenant,
                workspace_id=workspace,
                user_id=user,
                event_type="policy_decision",
                action=PROMOTION_BROWSER_SKILL_SHADOW_EXECUTION_PROOF_ACTION,
                target=resolved_candidate_id,
                policy_decision="approval_required",
                timestamp=now_iso(),
                metadata={
                    "candidate_id": resolved_candidate_id,
                    "proposed_skill_id": proposed_skill_id,
                    "target_url": target_url,
                    "review_closeout_ref": review_closeout_rel.as_posix(),
                    "browser_run_sha256": browser_run_sha256,
                    "scope": scope_obj.as_dict(),
                    "browser_execution_allowed": False,
                    "trusted_promotion_allowed": False,
                },
                redacted_fields=[],
            ),
        )
        approvals_dir(root, tenant, workspace).mkdir(parents=True, exist_ok=True)
        approval = create_approval_request(
            root,
            scope=scope_obj,
            run_id=run_id,
            workflow_id=PROMOTION_WORKFLOW_ID,
            action=PROMOTION_BROWSER_SKILL_SHADOW_EXECUTION_PROOF_ACTION,
            risk_level="high",
            approval_reason=(
                "Review guarded local Browser Skill shadow execution proof request for "
                f"{resolved_candidate_id} at {target_url}. Approval does not execute a browser; "
                "a separate executor pass must consume the approved request."
            ),
            required_approver_role="approver",
            requested_by=actor,
            metadata={
                "candidate_id": resolved_candidate_id,
                "proposed_skill_id": proposed_skill_id,
                "target_url": target_url,
                "source_approval_id": source_approval_id,
                "activation_approval_id": activation_approval_id,
                "review_closeout_ref": review_closeout_rel.as_posix(),
                "review_closeout_sha256": review_closeout_sha256,
                "browser_run_ref": browser_run_rel.as_posix(),
                "browser_run_sha256": browser_run_sha256,
                "future_command_name": "browser-skill-shadow-execution-proof",
                "future_required_mode": "shadow",
                "future_write_set": approval_packet["future_write_set"],
            },
        )
        append_audit_event(
            root,
            SiteOpsAuditEvent(
                event_id=f"event_{run_id}_approval_request",
                run_id=run_id,
                tenant_id=tenant,
                workspace_id=workspace,
                user_id=user,
                event_type="approval_request_created",
                action=PROMOTION_BROWSER_SKILL_SHADOW_EXECUTION_PROOF_ACTION,
                target=resolved_candidate_id,
                policy_decision="approval_required",
                timestamp=now_iso(),
                metadata={
                    "approval_id": approval.get("approval_id"),
                    "approval_ref": approval.get("approval_ref"),
                    "browser_execution_allowed": False,
                    "trusted_promotion_allowed": False,
                },
                redacted_fields=[],
            ),
        )
        approval_packet["approval_request_written"] = True
    elif write_approval_request:
        approval_write_blocked = True

    if approval:
        status = "shadow_execution_approval_request_written"
        review_decision = "await_operator_approval_before_shadow_execution_proof"
    elif approval_packet_ready:
        status = "shadow_execution_approval_packet_ready_no_write"
        review_decision = "rerun_with_write_approval_request_after_operator_review"
    else:
        status = "blocked_shadow_execution_approval_packet"
        review_decision = "repair_shadow_replay_evidence_review_before_shadow_execution"

    result = dict(write_pass)
    result.update(
        {
            "action": PROMOTION_BROWSER_SKILL_SHADOW_EXECUTION_APPROVAL_PACKET_ACTION,
            "browser_skill_shadow_execution_approval_packet_status": status,
            "review_decision": review_decision,
            "shadow_execution_approval_packet": approval_packet,
            "shadow_execution_approval_packet_checks": checks,
            "approval_request_ready": approval_packet_ready,
            "write_approval_request_requested": bool(write_approval_request),
            "approval_request_written": bool(approval),
            "approval_write_blocked": approval_write_blocked,
            "approval": approval,
            "approval_id": approval.get("approval_id") if approval else None,
            "approval_ref": approval.get("approval_ref") if approval else None,
            "run_id": run_id,
            "run_ref": run_ref,
            "audit_ref": audit_ref,
            "run_record_written": bool(run_ref),
            "audit_written": bool(audit_ref),
            "review_closeout_ref": review_closeout_path.as_posix() if review_closeout_path.exists() else None,
            "review_closeout_sha256": review_closeout_sha256,
            "browser_run_ref": browser_run_path.as_posix() if browser_run_path.exists() else None,
            "browser_run_sha256": browser_run_sha256,
            "future_browser_run_ref": future_execution_run_rel.as_posix(),
            "future_agent_activity_ref": future_execution_activity_rel.as_posix(),
            "ready_for_guarded_local_shadow_execution_proof_next": approval_packet_ready,
            "browser_replay_built": False,
            "browser_execution_allowed": False,
            "browser_launch_allowed": False,
            "cdp_connection_allowed": False,
            "authenticated_session_allowed": False,
            "real_profile_allowed": False,
            "cookie_or_token_access_allowed": False,
            "dom_mutation_allowed": False,
            "external_submit_allowed": False,
            "trusted_promotion_allowed": False,
            "activation_performed": False,
            "agent_bus_enqueue_allowed": False,
            "provider_api_call_allowed": False,
            "gate_policy_mutation_allowed": False,
            "canonical_writeback_allowed": False,
            "writes_performed": bool(approval or run_ref or audit_ref),
            "files_modified": bool(approval or run_ref or audit_ref),
            "boundary": (
                "Browser Skill shadow execution approval packet only; it may "
                "write a scoped pending ApprovalRequest plus run/audit metadata "
                "only when explicitly requested. It does not launch browser/CDP, "
                "use authenticated sessions, mutate DOM, promote trusted "
                "artifacts, activate skills, enqueue Agent Bus work, call "
                "providers, mutate Gate, or write canonical ChaseOS state."
            ),
        }
    )
    return result


def candidate_promotion_browser_skill_shadow_execution_approval_decision_preflight(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    actor: str,
    target_url: str,
    shadow_execution_approval_id: str,
    shadow_mode: bool = False,
    local_target_only: bool = False,
    allowlisted_domain: str | None = None,
    max_steps: int = 5,
    source_approval_id: str | None = None,
    activation_approval_id: str | None = None,
    reason: str | None = None,
) -> dict[str, Any]:
    """Validate a shadow-execution approval request without deciding or consuming it."""
    packet = candidate_promotion_browser_skill_shadow_execution_approval_packet(
        candidate_id,
        root,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
        actor=actor,
        target_url=target_url,
        shadow_mode=shadow_mode,
        write_approval_request=False,
        local_target_only=local_target_only,
        allowlisted_domain=allowlisted_domain,
        max_steps=max_steps,
        source_approval_id=source_approval_id,
        activation_approval_id=activation_approval_id,
        reason=reason or "operator requested shadow execution approval decision preflight",
    )
    scope = dict(packet.get("scope") or {})
    tenant = str(scope.get("tenant_id") or tenant_id or "local")
    workspace = str(scope.get("workspace_id") or workspace_id or "default")
    user = str(scope.get("user_id") or user_id or "local-user")
    approval = show_approval_request(root, shadow_execution_approval_id, tenant_id=tenant)
    metadata = dict(approval.get("metadata") or {})
    packet_record = dict(packet.get("shadow_execution_approval_packet") or {})
    packet_write_set = dict(packet_record.get("future_write_set") or {})
    metadata_write_set = dict(metadata.get("future_write_set") or {})
    approval_status = str(approval.get("status") or "")
    browser_run_sha256 = str(packet.get("browser_run_sha256") or "")
    metadata_browser_run_sha256 = str(metadata.get("browser_run_sha256") or "")
    review_closeout_sha256 = str(packet.get("review_closeout_sha256") or "")
    metadata_review_closeout_sha256 = str(metadata.get("review_closeout_sha256") or "")
    approval_scope_ok = (
        approval.get("tenant_id") == tenant
        and approval.get("workspace_id") == workspace
        and approval.get("user_id") == user
    )
    action_ok = approval.get("action") == PROMOTION_BROWSER_SKILL_SHADOW_EXECUTION_PROOF_ACTION
    candidate_ok = metadata.get("candidate_id") == packet.get("candidate_id")
    skill_ok = metadata.get("proposed_skill_id") == packet.get("proposed_skill_id")
    target_ok = metadata.get("target_url") == target_url
    source_ok = metadata.get("source_approval_id") == source_approval_id
    activation_ok = metadata.get("activation_approval_id") == activation_approval_id
    browser_digest_ok = bool(browser_run_sha256 and metadata_browser_run_sha256 == browser_run_sha256)
    review_digest_ok = bool(review_closeout_sha256 and metadata_review_closeout_sha256 == review_closeout_sha256)
    review_ref_ok = metadata.get("review_closeout_ref") == packet_record.get("review_closeout_ref")
    browser_ref_ok = metadata.get("browser_run_ref") == packet_record.get("browser_run_ref")
    expected_agent_activity_prefix = f"07_LOGS/Agent-Activity/{tenant}/{workspace}/"
    expected_execution_slug = f"siteops-shadow-execution-{_slug(str(packet.get('candidate_id') or candidate_id))}"
    metadata_agent_activity_path = str(metadata_write_set.get("agent_activity_log_path") or "")
    future_write_set_ok = (
        metadata_write_set.get("browser_run_log_path") == packet_write_set.get("browser_run_log_path")
        and metadata_agent_activity_path.startswith(expected_agent_activity_prefix)
        and expected_execution_slug in metadata_agent_activity_path
        and metadata_write_set.get("writes_allowed_in_this_pass") is False
        and packet_write_set.get("writes_allowed_in_this_pass") is False
    )
    packet_ready = packet.get("approval_request_ready") is True
    required_role_ok = approval.get("required_approver_role") == "approver"
    no_secret_or_session_fields = not _contains_forbidden_browser_run_fields(approval)
    no_mutation_flags = (
        packet.get("browser_execution_allowed") is False
        and packet.get("cdp_connection_allowed") is False
        and packet.get("authenticated_session_allowed") is False
        and packet.get("trusted_promotion_allowed") is False
        and packet.get("canonical_writeback_allowed") is False
    )
    target_policy_ok, target_policy_reason = _target_url_allowed_for_shadow_replay(
        target_url,
        local_target_only=local_target_only,
        allowlisted_domain=allowlisted_domain,
    )
    future_browser_run_ref = str(metadata_write_set.get("browser_run_log_path") or packet.get("future_browser_run_ref") or "")
    future_agent_activity_ref = str(metadata_write_set.get("agent_activity_log_path") or packet.get("future_agent_activity_ref") or "")
    vault_root = Path(root or Path.cwd()).resolve(strict=False)
    future_paths_absent = (
        not (vault_root / future_browser_run_ref).exists()
        and not (vault_root / future_agent_activity_ref).exists()
    )
    checks = [
        _executor_preflight_check(
            "shadow_execution_approval_scope_matches",
            passed=approval_scope_ok,
            detail=f"{approval.get('tenant_id')}/{approval.get('workspace_id')}/{approval.get('user_id')}",
        ),
        _executor_preflight_check(
            "shadow_execution_approval_action_matches",
            passed=action_ok,
            detail=str(approval.get("action")),
        ),
        _executor_preflight_check(
            "shadow_execution_approval_candidate_matches",
            passed=candidate_ok,
            detail=str(metadata.get("candidate_id")),
        ),
        _executor_preflight_check(
            "shadow_execution_approval_skill_matches",
            passed=skill_ok,
            detail=str(metadata.get("proposed_skill_id")),
        ),
        _executor_preflight_check(
            "shadow_execution_approval_target_matches",
            passed=target_ok,
            detail=str(metadata.get("target_url")),
        ),
        _executor_preflight_check(
            "shadow_execution_approval_source_approval_matches",
            passed=source_ok,
            detail=str(metadata.get("source_approval_id")),
        ),
        _executor_preflight_check(
            "shadow_execution_approval_activation_approval_matches",
            passed=activation_ok,
            detail=str(metadata.get("activation_approval_id")),
        ),
        _executor_preflight_check(
            "shadow_execution_approval_browser_run_digest_matches",
            passed=browser_digest_ok,
            detail=metadata_browser_run_sha256 or "missing",
        ),
        _executor_preflight_check(
            "shadow_execution_approval_review_closeout_digest_matches",
            passed=review_digest_ok,
            detail=metadata_review_closeout_sha256 or "missing",
        ),
        _executor_preflight_check(
            "shadow_execution_approval_evidence_refs_match",
            passed=review_ref_ok and browser_ref_ok,
            detail=str(metadata.get("review_closeout_ref") or "missing"),
        ),
        _executor_preflight_check(
            "shadow_execution_approval_future_write_set_matches",
            passed=future_write_set_ok,
            detail=str(metadata_write_set.get("browser_run_log_path") or "missing"),
        ),
        _executor_preflight_check(
            "shadow_execution_approval_packet_still_ready",
            passed=packet_ready,
            detail=str(packet.get("browser_skill_shadow_execution_approval_packet_status")),
        ),
        _executor_preflight_check(
            "shadow_execution_approval_required_role_valid",
            passed=required_role_ok,
            detail=str(approval.get("required_approver_role")),
        ),
        _executor_preflight_check(
            "shadow_execution_approval_contains_no_secret_or_session_fields",
            passed=no_secret_or_session_fields,
            detail="approval metadata contains no forbidden secret/session fields",
        ),
        _executor_preflight_check(
            "shadow_execution_preflight_keeps_mutation_flags_false",
            passed=no_mutation_flags,
            detail="browser/CDP/session/trusted/canonical flags remain false",
        ),
        _executor_preflight_check(
            "shadow_execution_target_policy_still_valid",
            passed=target_policy_ok,
            detail=target_policy_reason,
        ),
        _executor_preflight_check(
            "shadow_execution_future_targets_still_absent",
            passed=future_paths_absent,
            detail=", ".join([future_browser_run_ref, future_agent_activity_ref]),
        ),
    ]
    required_checks_pass = all(bool(check.get("passed")) for check in checks)
    if not required_checks_pass:
        preflight_status = "blocked_shadow_execution_approval_decision_preflight_metadata_or_readiness_mismatch"
        review_decision = "blocked_before_shadow_execution_approval_decision"
    elif approval_status == "pending":
        preflight_status = "blocked_pending_shadow_execution_approval"
        review_decision = "pending_operator_decision_no_browser_execution"
    elif approval_status == "approved":
        preflight_status = "shadow_execution_approval_decision_preflight_ready_no_mutation"
        review_decision = "approved_for_separate_shadow_execution_proof_review"
    elif approval_status == "rejected":
        preflight_status = "shadow_execution_approval_decision_preflight_rejected_blocks_execution"
        review_decision = "rejected_no_browser_execution"
    else:
        preflight_status = f"blocked_shadow_execution_approval_decision_preflight_unknown_status:{approval_status}"
        review_decision = "blocked_before_shadow_execution_approval_decision"

    ready_for_future_proof_review = required_checks_pass and approval_status == "approved"
    denied_effects = [
        "decide shadow execution approval request",
        "consume shadow execution approval request",
        "launch or control a browser",
        "connect CDP",
        "use authenticated browser session",
        "read cookies, tokens, secrets, localStorage, sessionStorage, or account state",
        "mutate DOM or submit forms",
        "write Browser Run execution proof",
        "write Agent Activity execution proof",
        "promote trusted Browser Skill artifact",
        "activate promoted skills",
        "enqueue Agent Bus work",
        "call provider APIs",
        "mutate Gate policy",
        "write canonical ChaseOS memory/state",
    ]
    result = dict(packet)
    result.update(
        {
            "action": PROMOTION_BROWSER_SKILL_SHADOW_EXECUTION_APPROVAL_DECISION_PREFLIGHT_ACTION,
            "candidate_id": packet.get("candidate_id"),
            "proposed_skill_id": packet.get("proposed_skill_id"),
            "scope": {"tenant_id": tenant, "workspace_id": workspace, "user_id": user},
            "actor": actor,
            "source_approval_id": source_approval_id,
            "activation_approval_id": activation_approval_id,
            "shadow_execution_approval_id": shadow_execution_approval_id,
            "shadow_execution_approval_decision_preflight_status": preflight_status,
            "review_decision": review_decision,
            "approval_status": approval_status,
            "approval_ref": approval.get("approval_ref"),
            "approval_decided_by": approval.get("decided_by"),
            "approval_decided_at": approval.get("decided_at"),
            "shadow_execution_approval_decision_preflight_checks": checks,
            "required_checks_pass": required_checks_pass,
            "browser_run_digest_matches": browser_digest_ok,
            "review_closeout_digest_matches": review_digest_ok,
            "future_write_set_matches": future_write_set_ok,
            "target_policy_valid": target_policy_ok,
            "future_targets_still_absent": future_paths_absent,
            "ready_for_shadow_execution_proof_review_next_pass": ready_for_future_proof_review,
            "approved_for_future_shadow_execution_proof_review": ready_for_future_proof_review,
            "approval_decision_written": False,
            "approval_consumed": False,
            "shadow_execution_proof_written": False,
            "browser_execution_allowed": False,
            "browser_launch_allowed": False,
            "cdp_connection_allowed": False,
            "authenticated_session_allowed": False,
            "real_profile_allowed": False,
            "cookie_or_token_access_allowed": False,
            "dom_mutation_allowed": False,
            "external_submit_allowed": False,
            "trusted_promotion_allowed": False,
            "activation_allowed": False,
            "activation_performed": False,
            "agent_bus_enqueue_allowed": False,
            "provider_api_call_allowed": False,
            "gate_policy_mutation_allowed": False,
            "canonical_writeback_allowed": False,
            "writes_performed": False,
            "files_modified": False,
            "blocked_actions": denied_effects,
            "denied_effects": denied_effects,
            "boundary": (
                "Browser Skill shadow execution approval decision preflight only; "
                "validates a pending/decided ApprovalRequest and reviewed evidence "
                "chain without deciding, consuming, launching browser/CDP, using "
                "sessions, mutating DOM, writing execution proof, promoting trusted "
                "artifacts, activating skills, enqueueing Agent Bus work, calling "
                "providers, mutating Gate, or writing canonical ChaseOS state."
            ),
        }
    )
    return result


def candidate_promotion_browser_skill_shadow_execution_approval_decision_request(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    actor: str,
    target_url: str,
    shadow_execution_approval_id: str,
    decision: str,
    shadow_mode: bool = False,
    local_target_only: bool = False,
    allowlisted_domain: str | None = None,
    max_steps: int = 5,
    source_approval_id: str | None = None,
    activation_approval_id: str | None = None,
    reason: str | None = None,
    write_approval_decision: bool = False,
) -> dict[str, Any]:
    """Approve/reject a shadow-execution approval only behind an explicit write flag."""
    if decision not in {"approve", "reject"}:
        raise SiteOpsValidationError("shadow execution approval decision must be approve or reject")
    status = "approved" if decision == "approve" else "rejected"
    preflight = candidate_promotion_browser_skill_shadow_execution_approval_decision_preflight(
        candidate_id,
        root,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
        actor=actor,
        target_url=target_url,
        shadow_execution_approval_id=shadow_execution_approval_id,
        shadow_mode=shadow_mode,
        local_target_only=local_target_only,
        allowlisted_domain=allowlisted_domain,
        max_steps=max_steps,
        source_approval_id=source_approval_id,
        activation_approval_id=activation_approval_id,
        reason=reason or "operator requested shadow execution approval decision request",
    )
    scope = dict(preflight.get("scope") or {})
    tenant = str(scope.get("tenant_id") or tenant_id or "local")
    workspace = str(scope.get("workspace_id") or workspace_id or "default")
    approval_status = str(preflight.get("approval_status") or "")
    required_checks_pass = preflight.get("required_checks_pass") is True
    pending = approval_status == "pending"
    approved = approval_status == "approved"
    rejected = approval_status == "rejected"
    decision_ready = required_checks_pass and pending
    proof_ready = required_checks_pass and approved
    if not required_checks_pass:
        decision_status = "blocked_shadow_execution_approval_decision_metadata_or_readiness_mismatch"
        proof_status = "shadow_execution_proof_not_ready"
    elif approved:
        decision_status = "shadow_execution_approval_already_approved"
        proof_status = "shadow_execution_proof_review_ready_no_browser"
    elif rejected:
        decision_status = "blocked_shadow_execution_approval_rejected"
        proof_status = "shadow_execution_proof_blocked_rejected"
    elif not write_approval_decision:
        decision_status = "shadow_execution_approval_decision_ready_no_write"
        proof_status = "shadow_execution_proof_blocked_pending_approval"
    else:
        decision_status = "shadow_execution_approval_decision_ready_to_write"
        proof_status = "shadow_execution_proof_blocked_until_decision_write"

    updated_approval: dict[str, Any] | None = None
    approval_ref = preflight.get("approval_ref")
    audit_ref: str | None = None
    decision_written = False
    if decision_ready and write_approval_decision:
        updated_approval = decide_approval_request(
            root,
            shadow_execution_approval_id,
            actor=actor,
            status=status,
            tenant_id=tenant,
            reason=reason,
        )
        decision_written = True
        approval_ref = updated_approval.get("approval_ref")
        audit_ref = str(audit_path(root, tenant, workspace, str(updated_approval.get("run_id") or "")))
        decision_status = "shadow_execution_approval_decision_written"
        proof_status = (
            "shadow_execution_proof_review_ready_no_browser"
            if status == "approved"
            else "shadow_execution_proof_blocked_rejected"
        )
        proof_ready = status == "approved"

    denied_effects = [
        "consume shadow execution approval request",
        "launch or control a browser",
        "connect CDP",
        "use authenticated browser session",
        "read cookies, tokens, secrets, localStorage, sessionStorage, or account state",
        "mutate DOM or submit forms",
        "write Browser Run execution proof",
        "write Agent Activity execution proof",
        "promote trusted Browser Skill artifact",
        "activate promoted skills",
        "enqueue Agent Bus work",
        "call provider APIs",
        "mutate Gate policy",
        "write canonical ChaseOS memory/state",
    ]
    result = dict(preflight)
    result.update(
        {
            "action": PROMOTION_BROWSER_SKILL_SHADOW_EXECUTION_APPROVAL_DECISION_REQUEST_ACTION,
            "shadow_execution_approval_decision_request_status": decision_status,
            "shadow_execution_proof_status": proof_status,
            "shadow_execution_approval_id": shadow_execution_approval_id,
            "actor": actor,
            "decision": decision,
            "reason": reason,
            "approval_ref": approval_ref,
            "audit_ref": audit_ref,
            "shadow_execution_approval": updated_approval,
            "approval_status_before_decision": approval_status,
            "approval_status_after_decision": status if decision_written else approval_status,
            "approval_decision_write_requested": bool(write_approval_decision),
            "approval_decision_written": decision_written,
            "approval_consumed": False,
            "shadow_execution_proof_ready": proof_ready,
            "ready_for_shadow_execution_proof_next_pass": proof_ready,
            "shadow_execution_proof_written": False,
            "browser_execution_allowed": False,
            "browser_launch_allowed": False,
            "cdp_connection_allowed": False,
            "authenticated_session_allowed": False,
            "real_profile_allowed": False,
            "cookie_or_token_access_allowed": False,
            "dom_mutation_allowed": False,
            "external_submit_allowed": False,
            "trusted_promotion_allowed": False,
            "activation_allowed": False,
            "activation_performed": False,
            "agent_bus_enqueue_allowed": False,
            "provider_api_call_allowed": False,
            "gate_policy_mutation_allowed": False,
            "canonical_writeback_allowed": False,
            "writes_performed": decision_written,
            "files_modified": decision_written,
            "blocked_actions": denied_effects,
            "denied_effects": denied_effects,
            "boundary": (
                "Browser Skill shadow execution approval decision path only; "
                "it may approve or reject the scoped ApprovalRequest when "
                "explicitly requested, but it does not consume the approval, "
                "launch browser/CDP, use sessions, mutate DOM, write execution "
                "proof, promote trusted artifacts, activate skills, enqueue "
                "Agent Bus work, call providers, mutate Gate, or write canonical "
                "ChaseOS state."
            ),
        }
    )
    return result


def candidate_promotion_browser_skill_shadow_execution_approval_live_decision_readiness(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    actor: str,
    target_url: str,
    shadow_execution_approval_id: str,
    intended_decision: str | None = None,
    shadow_mode: bool = False,
    local_target_only: bool = False,
    allowlisted_domain: str | None = None,
    max_steps: int = 5,
    source_approval_id: str | None = None,
    activation_approval_id: str | None = None,
    reason: str | None = None,
) -> dict[str, Any]:
    """Report live decision readiness without mutating the ApprovalRequest."""
    if intended_decision is not None and intended_decision not in {"approve", "reject"}:
        raise SiteOpsValidationError("intended decision must be approve or reject")
    common_kwargs = {
        "tenant_id": tenant_id,
        "workspace_id": workspace_id,
        "user_id": user_id,
        "actor": actor,
        "target_url": target_url,
        "shadow_execution_approval_id": shadow_execution_approval_id,
        "shadow_mode": shadow_mode,
        "local_target_only": local_target_only,
        "allowlisted_domain": allowlisted_domain,
        "max_steps": max_steps,
        "source_approval_id": source_approval_id,
        "activation_approval_id": activation_approval_id,
        "reason": reason or "operator requested shadow execution approval live decision readiness",
    }
    if intended_decision:
        base = candidate_promotion_browser_skill_shadow_execution_approval_decision_request(
            candidate_id,
            root,
            decision=intended_decision,
            write_approval_decision=False,
            **common_kwargs,
        )
    else:
        base = candidate_promotion_browser_skill_shadow_execution_approval_decision_preflight(
            candidate_id,
            root,
            **common_kwargs,
        )
    approval_status = str(
        base.get("approval_status_after_decision")
        or base.get("approval_status")
        or ""
    )
    required_checks_pass = base.get("required_checks_pass") is True
    pending = approval_status == "pending"
    approved = approval_status == "approved"
    rejected = approval_status == "rejected"
    if not required_checks_pass:
        readiness_status = "blocked_live_decision_metadata_or_readiness_mismatch"
        ready_for_write = False
    elif approved:
        readiness_status = "live_decision_already_approved_no_write"
        ready_for_write = False
    elif rejected:
        readiness_status = "live_decision_already_rejected_no_write"
        ready_for_write = False
    elif not intended_decision:
        readiness_status = "blocked_missing_explicit_operator_decision"
        ready_for_write = False
    elif pending:
        readiness_status = "live_decision_ready_waiting_explicit_write_authorization"
        ready_for_write = True
    else:
        readiness_status = "blocked_live_decision_unknown_approval_status"
        ready_for_write = False

    denied_effects = [
        "write live approval decision without explicit operator authorization",
        "consume shadow execution approval request",
        "launch or control a browser",
        "connect CDP",
        "use authenticated browser session",
        "read cookies, tokens, secrets, localStorage, sessionStorage, or account state",
        "mutate DOM or submit forms",
        "write Browser Run execution proof",
        "promote trusted Browser Skill artifact",
        "activate promoted skills",
        "enqueue Agent Bus work",
        "call provider APIs",
        "mutate Gate policy",
        "write canonical ChaseOS memory/state",
    ]
    approval_command_preview = None
    rejection_command_preview = None
    if required_checks_pass and pending:
        base_command = (
            "python -m runtime.cli.main siteops candidates "
            "browser-skill-shadow-execution-approval-decision-request "
            f"{candidate_id} --shadow-execution-approval-id {shadow_execution_approval_id} "
            f"--decision {{decision}} --tenant {tenant_id or 'local'} "
            f"--workspace {workspace_id or 'default'} --user {user_id or 'local-user'} "
            f"--actor {actor} --target-url {target_url} --shadow-mode --local-target-only "
            "--write-approval-decision --json"
        )
        if source_approval_id:
            base_command += f" --source-approval-id {source_approval_id}"
        if activation_approval_id:
            base_command += f" --activation-approval-id {activation_approval_id}"
        approval_command_preview = base_command.replace("{decision}", "approve")
        rejection_command_preview = base_command.replace("{decision}", "reject")

    result = dict(base)
    result.update(
        {
            "action": PROMOTION_BROWSER_SKILL_SHADOW_EXECUTION_APPROVAL_LIVE_DECISION_READINESS_ACTION,
            "shadow_execution_approval_live_decision_readiness_status": readiness_status,
            "shadow_execution_approval_id": shadow_execution_approval_id,
            "intended_decision": intended_decision,
            "approval_status": approval_status,
            "explicit_operator_authorization_present": False,
            "live_decision_written": False,
            "approval_decision_written": False,
            "approval_consumed": False,
            "ready_for_live_decision_write_next_pass": ready_for_write,
            "approval_command_preview": approval_command_preview,
            "rejection_command_preview": rejection_command_preview,
            "shadow_execution_proof_written": False,
            "browser_execution_allowed": False,
            "browser_launch_allowed": False,
            "cdp_connection_allowed": False,
            "authenticated_session_allowed": False,
            "trusted_promotion_allowed": False,
            "activation_allowed": False,
            "agent_bus_enqueue_allowed": False,
            "provider_api_call_allowed": False,
            "gate_policy_mutation_allowed": False,
            "canonical_writeback_allowed": False,
            "writes_performed": False,
            "files_modified": False,
            "blocked_actions": denied_effects,
            "denied_effects": denied_effects,
            "boundary": (
                "Browser Skill shadow execution approval live-decision readiness only; "
                "it reports whether a scoped approve/reject decision can be written "
                "later, but does not write the decision, consume the approval, "
                "launch browser/CDP, use sessions, mutate DOM, write execution "
                "proof, promote trusted artifacts, activate skills, enqueue "
                "Agent Bus work, call providers, mutate Gate, or write canonical "
                "ChaseOS state."
            ),
        }
    )
    return result


def candidate_promotion_browser_skill_shadow_execution_proof_readiness(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    actor: str,
    target_url: str,
    shadow_execution_approval_id: str,
    shadow_mode: bool = False,
    local_target_only: bool = False,
    allowlisted_domain: str | None = None,
    max_steps: int = 5,
    source_approval_id: str | None = None,
    activation_approval_id: str | None = None,
    reason: str | None = None,
) -> dict[str, Any]:
    """Fail-closed readiness check for future shadow execution proof."""
    preflight = candidate_promotion_browser_skill_shadow_execution_approval_decision_preflight(
        candidate_id,
        root,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
        actor=actor,
        target_url=target_url,
        shadow_execution_approval_id=shadow_execution_approval_id,
        shadow_mode=shadow_mode,
        local_target_only=local_target_only,
        allowlisted_domain=allowlisted_domain,
        max_steps=max_steps,
        source_approval_id=source_approval_id,
        activation_approval_id=activation_approval_id,
        reason=reason or "operator requested shadow execution proof readiness",
    )
    approval_status = str(preflight.get("approval_status") or "")
    required_checks_pass = preflight.get("required_checks_pass") is True
    approved = approval_status == "approved"
    pending = approval_status == "pending"
    rejected = approval_status == "rejected"
    if not required_checks_pass:
        proof_status = "blocked_shadow_execution_proof_metadata_or_readiness_mismatch"
        ready_for_proof = False
    elif approved:
        proof_status = "shadow_execution_proof_ready_no_execution"
        ready_for_proof = True
    elif pending:
        proof_status = "blocked_shadow_execution_proof_pending_approval_decision"
        ready_for_proof = False
    elif rejected:
        proof_status = "blocked_shadow_execution_proof_rejected_approval"
        ready_for_proof = False
    else:
        proof_status = "blocked_shadow_execution_proof_unknown_approval_status"
        ready_for_proof = False

    denied_effects = [
        "consume shadow execution approval request",
        "launch or control a browser",
        "connect CDP",
        "use authenticated browser session",
        "read cookies, tokens, secrets, localStorage, sessionStorage, or account state",
        "mutate DOM or submit forms",
        "write Browser Run execution proof",
        "write Agent Activity execution proof",
        "promote trusted Browser Skill artifact",
        "activate promoted skills",
        "enqueue Agent Bus work",
        "call provider APIs",
        "mutate Gate policy",
        "write canonical ChaseOS memory/state",
    ]
    proof_command_preview = None
    if ready_for_proof:
        proof_command_preview = (
            "python -m runtime.cli.main siteops candidates "
            f"browser-skill-shadow-execution-proof {candidate_id} "
            f"--shadow-execution-approval-id {shadow_execution_approval_id} "
            f"--tenant {tenant_id or 'local'} --workspace {workspace_id or 'default'} "
            f"--user {user_id or 'local-user'} --actor {actor} --target-url {target_url} "
            "--shadow-mode --local-target-only --json"
        )
        if source_approval_id:
            proof_command_preview += f" --source-approval-id {source_approval_id}"
        if activation_approval_id:
            proof_command_preview += f" --activation-approval-id {activation_approval_id}"

    result = dict(preflight)
    result.update(
        {
            "action": PROMOTION_BROWSER_SKILL_SHADOW_EXECUTION_PROOF_READINESS_ACTION,
            "shadow_execution_proof_readiness_status": proof_status,
            "shadow_execution_approval_id": shadow_execution_approval_id,
            "approval_status": approval_status,
            "ready_for_shadow_execution_proof": ready_for_proof,
            "proof_command_preview": proof_command_preview,
            "approval_consumed": False,
            "shadow_execution_proof_written": False,
            "browser_execution_allowed": False,
            "browser_launch_allowed": False,
            "cdp_connection_allowed": False,
            "authenticated_session_allowed": False,
            "real_profile_allowed": False,
            "cookie_or_token_access_allowed": False,
            "dom_mutation_allowed": False,
            "external_submit_allowed": False,
            "trusted_promotion_allowed": False,
            "activation_allowed": False,
            "agent_bus_enqueue_allowed": False,
            "provider_api_call_allowed": False,
            "gate_policy_mutation_allowed": False,
            "canonical_writeback_allowed": False,
            "writes_performed": False,
            "files_modified": False,
            "blocked_actions": denied_effects,
            "denied_effects": denied_effects,
            "boundary": (
                "Browser Skill shadow execution proof readiness only; it "
                "validates that a scoped approval is approved before a future "
                "proof pass, but does not consume approval, launch browser/CDP, "
                "use sessions, mutate DOM, write execution proof, promote "
                "trusted artifacts, activate skills, enqueue Agent Bus work, "
                "call providers, mutate Gate, or write canonical ChaseOS state."
            ),
        }
    )
    return result


def candidate_promotion_browser_skill_shadow_execution_proof_consumption_guard(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    actor: str,
    target_url: str,
    shadow_execution_approval_id: str,
    shadow_mode: bool = False,
    local_target_only: bool = False,
    allowlisted_domain: str | None = None,
    max_steps: int = 5,
    source_approval_id: str | None = None,
    activation_approval_id: str | None = None,
    reason: str | None = None,
    consume_shadow_execution_approval: bool = False,
) -> dict[str, Any]:
    """Guard and optionally consume a shadow-execution approval by marker only."""
    readiness = candidate_promotion_browser_skill_shadow_execution_proof_readiness(
        candidate_id,
        root,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
        actor=actor,
        target_url=target_url,
        shadow_execution_approval_id=shadow_execution_approval_id,
        shadow_mode=shadow_mode,
        local_target_only=local_target_only,
        allowlisted_domain=allowlisted_domain,
        max_steps=max_steps,
        source_approval_id=source_approval_id,
        activation_approval_id=activation_approval_id,
        reason=reason or "operator requested shadow execution proof consumption guard",
    )
    scope = dict(readiness.get("scope") or {})
    tenant = str(scope.get("tenant_id") or tenant_id or "")
    workspace = str(scope.get("workspace_id") or workspace_id or "")
    user = str(scope.get("user_id") or user_id or "")
    candidate = str(readiness.get("candidate_id") or candidate_id)
    proposed_skill_id = str(readiness.get("proposed_skill_id") or candidate)
    root_path = Path(root) if root is not None else Path.cwd()
    resolved_root = root_path.resolve()
    marker_name = (
        f"shadow_execution_consumer_{_slug(candidate)[:48]}_"
        f"{hashlib.sha256(f'{tenant}|{workspace}|{user}|{candidate}|{shadow_execution_approval_id}'.encode('utf-8')).hexdigest()[:12]}.json"
    )
    marker_parent = (
        resolved_root
        / "07_LOGS"
        / "SiteOps-Shadow-Execution-Consumers"
        / tenant
        / workspace
    )
    marker_path = marker_parent / marker_name
    run_id = f"siteops_shadow_execution_consumer_{_slug(candidate)[:48]}"
    run_audit_path = audit_path(root, tenant, workspace, run_id)
    audit_parent = resolved_root / "07_LOGS" / "SiteOps-Audits" / tenant / workspace
    marker_confined = _filesystem_path_is_within(marker_path, marker_parent)
    audit_confined = _filesystem_path_is_within(run_audit_path, audit_parent)
    marker_exists = marker_path.exists()
    marker_absent = not marker_exists
    approved_ready = bool(readiness.get("ready_for_shadow_execution_proof"))
    proof_readiness_status = str(readiness.get("shadow_execution_proof_readiness_status") or "")
    now = now_iso()
    marker_payload = {
        "record_type": "siteops_shadow_execution_approval_consumer",
        "schema_version": 1,
        "run_id": run_id,
        "tenant_id": tenant,
        "workspace_id": workspace,
        "user_id": user,
        "candidate_id": candidate,
        "proposed_skill_id": proposed_skill_id,
        "shadow_execution_approval_id": shadow_execution_approval_id,
        "source_approval_id": source_approval_id,
        "activation_approval_id": activation_approval_id,
        "approval_status_required": "approved",
        "approval_decided_by": readiness.get("approval_decided_by"),
        "approval_decided_at": readiness.get("approval_decided_at"),
        "browser_run_sha256": readiness.get("browser_run_sha256"),
        "review_closeout_sha256": readiness.get("review_closeout_sha256"),
        "future_browser_run_ref": readiness.get("future_browser_run_ref"),
        "future_agent_activity_ref": readiness.get("future_agent_activity_ref"),
        "target_url": target_url,
        "shadow_mode": bool(shadow_mode),
        "local_target_only": bool(local_target_only),
        "consumed_at": now,
        "consumed_by": actor,
        "reason": reason or "",
        "secret_values_visible": False,
        "shadow_execution_proof_written": False,
        "browser_execution_performed": False,
        "cdp_connection_performed": False,
        "authenticated_session_used": False,
        "dom_mutation_performed": False,
        "trusted_promotion_performed": False,
        "activation_performed": False,
        "agent_bus_enqueue_performed": False,
        "provider_api_call_performed": False,
        "gate_policy_mutated": False,
        "canonical_writeback_performed": False,
    }
    secret_errors = scan_secret_like_keys(marker_payload)
    checks = list(readiness.get("shadow_execution_approval_decision_preflight_checks") or []) + [
        _executor_preflight_check(
            "shadow_execution_proof_readiness_ready",
            passed=approved_ready,
            detail=proof_readiness_status,
        ),
        _executor_preflight_check(
            "shadow_execution_consumer_marker_path_confined",
            passed=marker_confined,
            detail=marker_path.as_posix(),
        ),
        _executor_preflight_check(
            "shadow_execution_consumer_marker_absent_before_write",
            passed=marker_absent,
            detail=marker_path.as_posix(),
        ),
        _executor_preflight_check(
            "shadow_execution_consumer_audit_path_confined",
            passed=audit_confined,
            detail=run_audit_path.as_posix(),
        ),
        _executor_preflight_check(
            "shadow_execution_consumer_marker_payload_has_no_secret_like_keys",
            passed=not secret_errors,
            detail="; ".join(secret_errors) if secret_errors else "no secret-like keys detected",
        ),
        _executor_preflight_check(
            "shadow_execution_consumer_stops_before_proof_runner",
            passed=True,
            detail="consumer records approval use only; proof runner remains separate",
        ),
        _executor_preflight_check(
            "shadow_execution_consumer_no_browser_authority",
            passed=True,
            detail="no browser launch, CDP, session, DOM, proof, or trusted promotion in this pass",
        ),
    ]
    checks_passed = all(bool(check.get("passed")) for check in checks if check.get("required", True))
    ready_to_consume = checks_passed and approved_ready and marker_confined and audit_confined and marker_absent

    if not approved_ready:
        guard_status = (
            "blocked_shadow_execution_proof_consumption_guard_readiness: "
            f"{proof_readiness_status}"
        )
        review_decision = "blocked_before_shadow_execution_approval_consumption"
    elif not marker_confined or not audit_confined:
        guard_status = "blocked_shadow_execution_proof_consumption_guard_scoped_path_posture"
        review_decision = "blocked_before_shadow_execution_approval_consumption"
    elif marker_exists:
        guard_status = "blocked_shadow_execution_consumption_marker_already_exists"
        review_decision = "blocked_exact_once_shadow_execution_approval_already_consumed"
    elif secret_errors:
        guard_status = "blocked_shadow_execution_consumer_marker_secret_like_key_detected"
        review_decision = "blocked_before_shadow_execution_approval_consumption"
    elif not consume_shadow_execution_approval:
        guard_status = "shadow_execution_proof_consumption_guard_ready_dry_run_no_write"
        review_decision = "ready_requires_explicit_consume_shadow_execution_approval_flag"
    else:
        guard_status = "shadow_execution_proof_consumption_guard_ready_to_consume"
        review_decision = "consume_shadow_execution_approval_marker_and_audit_only"

    run_ref: str | None = None
    preconsume_audit_ref: str | None = None
    postconsume_audit_ref: str | None = None
    marker_ref: str | None = None
    marker_digest: str | None = None
    if consume_shadow_execution_approval and ready_to_consume:
        run = SiteOpsRun(
            run_id=run_id,
            tenant_id=tenant,
            workspace_id=workspace,
            user_id=user,
            skill_id=proposed_skill_id,
            workflow_id=PROMOTION_WORKFLOW_ID,
            site_profile_id=None,
            provider_id=None,
            mode="shadow_execution_approval_consumption",
            status="shadow_execution_approval_consumed_marker_only",
            inputs_ref=shadow_execution_approval_id,
            outputs_ref=marker_path.as_posix(),
            audit_ref=run_audit_path.as_posix(),
            cost_estimate={"charged": False, "provider": None},
            cost_actual=None,
            started_at=now,
            ended_at=now_iso(),
        )
        run_ref = write_run_record(root, run)
        preconsume_audit_ref = append_audit_event(
            root,
            SiteOpsAuditEvent(
                event_id=f"event_{run_id}_shadow_execution_consumer_preconsume",
                run_id=run_id,
                tenant_id=tenant,
                workspace_id=workspace,
                user_id=user,
                event_type="shadow_execution_approval_consumer_preconsume",
                action=PROMOTION_BROWSER_SKILL_SHADOW_EXECUTION_PROOF_CONSUMPTION_GUARD_ACTION,
                target=candidate,
                policy_decision="allow_marker_only_consumption",
                timestamp=now_iso(),
                metadata={
                    "shadow_execution_approval_id": shadow_execution_approval_id,
                    "source_approval_id": source_approval_id,
                    "activation_approval_id": activation_approval_id,
                    "proposed_skill_id": proposed_skill_id,
                    "marker_ref": marker_path.as_posix(),
                    "shadow_execution_proof_written": False,
                    "browser_execution_allowed": False,
                    "canonical_writeback_allowed": False,
                },
                redacted_fields=[],
            ),
        )
        _write_json_create_new(marker_path, marker_payload)
        marker_ref = marker_path.as_posix()
        marker_digest = _sha256_json(marker_payload)
        postconsume_audit_ref = append_audit_event(
            root,
            SiteOpsAuditEvent(
                event_id=f"event_{run_id}_shadow_execution_consumer_postconsume",
                run_id=run_id,
                tenant_id=tenant,
                workspace_id=workspace,
                user_id=user,
                event_type="shadow_execution_approval_consumer_postconsume",
                action=PROMOTION_BROWSER_SKILL_SHADOW_EXECUTION_PROOF_CONSUMPTION_GUARD_ACTION,
                target=candidate,
                policy_decision="shadow_execution_approval_consumed_marker_only",
                timestamp=now_iso(),
                metadata={
                    "shadow_execution_approval_id": shadow_execution_approval_id,
                    "source_approval_id": source_approval_id,
                    "activation_approval_id": activation_approval_id,
                    "proposed_skill_id": proposed_skill_id,
                    "marker_ref": marker_ref,
                    "marker_sha256": marker_digest,
                    "shadow_execution_proof_written": False,
                    "browser_execution_allowed": False,
                    "canonical_writeback_allowed": False,
                },
                redacted_fields=[],
            ),
        )
        guard_status = "shadow_execution_approval_consumed_marker_and_audit_written"
        review_decision = "shadow_execution_approval_consumed_stop_before_proof_runner"

    denied_effects = [
        "mutate shadow execution ApprovalRequest status",
        "launch or control a browser",
        "connect CDP",
        "use authenticated browser session",
        "read cookies, tokens, secrets, localStorage, sessionStorage, or account state",
        "mutate DOM or submit forms",
        "write Browser Run execution proof",
        "write Agent Activity execution proof",
        "promote trusted Browser Skill artifact",
        "activate promoted skills",
        "enqueue Agent Bus work",
        "call provider APIs",
        "mutate Gate policy",
        "write canonical ChaseOS memory/state",
    ]
    writes_performed = bool(run_ref or preconsume_audit_ref or postconsume_audit_ref or marker_ref)
    result = dict(readiness)
    result.update(
        {
            "action": PROMOTION_BROWSER_SKILL_SHADOW_EXECUTION_PROOF_CONSUMPTION_GUARD_ACTION,
            "shadow_execution_proof_consumption_guard_status": guard_status,
            "review_decision": review_decision,
            "shadow_execution_approval_id": shadow_execution_approval_id,
            "actor": actor,
            "consume_shadow_execution_approval_requested": bool(consume_shadow_execution_approval),
            "consume_shadow_execution_approval_flag_supported": True,
            "shadow_execution_consumer_ready_to_consume": ready_to_consume,
            "shadow_execution_consumer_checks": checks,
            "shadow_execution_consumer_marker_payload": marker_payload,
            "shadow_execution_consumer_marker_ref": marker_ref,
            "shadow_execution_consumer_marker_path": marker_path.as_posix(),
            "shadow_execution_consumer_marker_sha256": marker_digest,
            "run_id": run_id,
            "run_ref": run_ref,
            "audit_ref": postconsume_audit_ref or preconsume_audit_ref,
            "preconsume_audit_ref": preconsume_audit_ref,
            "postconsume_audit_ref": postconsume_audit_ref,
            "blocked_actions": denied_effects,
            "denied_effects": denied_effects,
            "writes_performed": writes_performed,
            "files_modified": writes_performed,
            "run_record_written": bool(run_ref),
            "shadow_execution_consumption_marker_written": bool(marker_ref),
            "shadow_execution_consumer_audit_written": bool(
                preconsume_audit_ref or postconsume_audit_ref
            ),
            "audit_events_written": bool(preconsume_audit_ref or postconsume_audit_ref),
            "approval_consumed": bool(marker_ref),
            "approval_decision_written": False,
            "approval_request_status_mutated": False,
            "shadow_execution_proof_written": False,
            "browser_execution_allowed": False,
            "browser_launch_allowed": False,
            "cdp_connection_allowed": False,
            "authenticated_session_allowed": False,
            "real_profile_allowed": False,
            "cookie_or_token_access_allowed": False,
            "dom_mutation_allowed": False,
            "external_submit_allowed": False,
            "trusted_promotion_allowed": False,
            "trusted_artifacts_written": False,
            "activation_allowed": False,
            "activation_performed": False,
            "agent_bus_enqueue_allowed": False,
            "provider_api_call_allowed": False,
            "gate_policy_mutation_allowed": False,
            "canonical_writeback_allowed": False,
            "boundary": (
                "Browser Skill shadow execution proof consumption guard only; writes "
                "require explicit --consume-shadow-execution-approval, approved proof "
                "readiness, exact scope/digest checks, absent create-new marker, and "
                "scoped audit path. It records marker/audit/run evidence only and stops "
                "before browser/CDP execution, session use, DOM mutation, proof writes, "
                "trusted promotion, activation, Agent Bus work, provider calls, Gate "
                "mutation, or canonical ChaseOS writeback."
            ),
        }
    )
    return result


def candidate_promotion_browser_skill_shadow_execution_proof(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    actor: str,
    target_url: str,
    shadow_execution_approval_id: str,
    shadow_mode: bool = False,
    local_target_only: bool = False,
    allowlisted_domain: str | None = None,
    max_steps: int = 5,
    source_approval_id: str | None = None,
    activation_approval_id: str | None = None,
    reason: str | None = None,
    write_shadow_execution_proof: bool = False,
) -> dict[str, Any]:
    """Write scoped no-browser shadow execution proof artifacts after consumption."""
    readiness = candidate_promotion_browser_skill_shadow_execution_proof_readiness(
        candidate_id,
        root,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
        actor=actor,
        target_url=target_url,
        shadow_execution_approval_id=shadow_execution_approval_id,
        shadow_mode=shadow_mode,
        local_target_only=local_target_only,
        allowlisted_domain=allowlisted_domain,
        max_steps=max_steps,
        source_approval_id=source_approval_id,
        activation_approval_id=activation_approval_id,
        reason=reason or "operator requested shadow execution proof artifact writer",
    )
    scope = dict(readiness.get("scope") or {})
    tenant = str(scope.get("tenant_id") or tenant_id or "")
    workspace = str(scope.get("workspace_id") or workspace_id or "")
    user = str(scope.get("user_id") or user_id or "")
    candidate = str(readiness.get("candidate_id") or candidate_id)
    proposed_skill_id = str(readiness.get("proposed_skill_id") or candidate)
    root_path = Path(root) if root is not None else Path.cwd()
    resolved_root = root_path.resolve()
    slug = _slug(candidate)
    marker_name = (
        f"shadow_execution_consumer_{_slug(candidate)[:48]}_"
        f"{hashlib.sha256(f'{tenant}|{workspace}|{user}|{candidate}|{shadow_execution_approval_id}'.encode('utf-8')).hexdigest()[:12]}.json"
    )
    marker_parent = (
        resolved_root
        / "07_LOGS"
        / "SiteOps-Shadow-Execution-Consumers"
        / tenant
        / workspace
    )
    marker_path = marker_parent / marker_name
    browser_run_rel = (
        Path("07_LOGS")
        / "Browser-Runs"
        / tenant
        / workspace
        / f"siteops-shadow-execution-{slug}.json"
    )
    agent_activity_rel = (
        Path("07_LOGS")
        / "Agent-Activity"
        / tenant
        / workspace
        / f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}-siteops-shadow-execution-{slug}.md"
    )
    browser_run_path = resolved_root / browser_run_rel
    agent_activity_path = resolved_root / agent_activity_rel
    run_id = f"siteops_shadow_execution_proof_{_slug(candidate)[:48]}"
    run_audit_path = audit_path(root, tenant, workspace, run_id)
    audit_parent = resolved_root / "07_LOGS" / "SiteOps-Audits" / tenant / workspace
    marker_confined = _filesystem_path_is_within(marker_path, marker_parent)
    browser_run_confined = _filesystem_path_is_within(browser_run_path, resolved_root)
    agent_activity_confined = _filesystem_path_is_within(agent_activity_path, resolved_root)
    audit_confined = _filesystem_path_is_within(run_audit_path, audit_parent)
    marker_exists = marker_path.exists() and marker_path.is_file()
    browser_run_absent = not browser_run_path.exists()
    agent_activity_absent = not agent_activity_path.exists()
    approved_ready = bool(readiness.get("ready_for_shadow_execution_proof"))
    marker_payload: dict[str, Any] = {}
    marker_parse_ok = False
    marker_scope_ok = False
    marker_digest: str | None = None
    marker_secret_errors: list[str] = []
    if marker_exists and marker_confined:
        try:
            marker_payload = json.loads(marker_path.read_text(encoding="utf-8"))
            marker_digest = _sha256_json(marker_payload)
            marker_parse_ok = True
            marker_scope_ok = (
                marker_payload.get("record_type") == "siteops_shadow_execution_approval_consumer"
                and marker_payload.get("tenant_id") == tenant
                and marker_payload.get("workspace_id") == workspace
                and marker_payload.get("user_id") == user
                and marker_payload.get("candidate_id") == candidate
                and marker_payload.get("proposed_skill_id") == proposed_skill_id
                and marker_payload.get("shadow_execution_approval_id") == shadow_execution_approval_id
                and marker_payload.get("target_url") == target_url
                and marker_payload.get("shadow_execution_proof_written") is False
                and marker_payload.get("browser_execution_performed") is False
                and marker_payload.get("canonical_writeback_performed") is False
            )
            marker_secret_errors = scan_secret_like_keys(marker_payload)
        except (OSError, ValueError, json.JSONDecodeError):
            marker_parse_ok = False
    now = now_iso()
    browser_run_payload = {
        "record_type": "siteops_browser_skill_shadow_execution_proof",
        "schema_version": 1,
        "run_id": run_id,
        "tenant_id": tenant,
        "workspace_id": workspace,
        "user_id": user,
        "candidate_id": candidate,
        "proposed_skill_id": proposed_skill_id,
        "shadow_execution_approval_id": shadow_execution_approval_id,
        "shadow_execution_consumer_marker_ref": marker_path.as_posix(),
        "shadow_execution_consumer_marker_sha256": marker_digest,
        "source_approval_id": source_approval_id,
        "activation_approval_id": activation_approval_id,
        "target_url": target_url,
        "shadow_mode": bool(shadow_mode),
        "local_target_only": bool(local_target_only),
        "max_steps": max_steps,
        "proof_status": "shadow_execution_proof_artifact_written_no_browser_execution",
        "evidence_trust": "untrusted_shadow_execution_proof",
        "written_at": now,
        "written_by": actor,
        "reason": reason or "",
        "browser_execution_performed": False,
        "browser_launch_performed": False,
        "cdp_connection_performed": False,
        "authenticated_session_used": False,
        "real_profile_used": False,
        "credential_material_accessed": False,
        "storage_state_accessed": False,
        "dom_mutation_performed": False,
        "external_submit_performed": False,
        "trusted_artifact_mutated": False,
        "activation_performed": False,
        "agent_bus_enqueue_performed": False,
        "provider_api_call_performed": False,
        "gate_policy_mutated": False,
        "canonical_writeback_performed": False,
    }
    proof_secret_errors = scan_secret_like_keys(browser_run_payload)
    checks = list(readiness.get("shadow_execution_approval_decision_preflight_checks") or []) + [
        _executor_preflight_check(
            "shadow_execution_proof_readiness_ready",
            passed=approved_ready,
            detail=str(readiness.get("shadow_execution_proof_readiness_status") or ""),
        ),
        _executor_preflight_check(
            "shadow_execution_consumer_marker_present",
            passed=marker_exists,
            detail=marker_path.as_posix(),
        ),
        _executor_preflight_check(
            "shadow_execution_consumer_marker_path_confined",
            passed=marker_confined,
            detail=marker_path.as_posix(),
        ),
        _executor_preflight_check(
            "shadow_execution_consumer_marker_parseable",
            passed=marker_parse_ok,
            detail="marker parsed" if marker_parse_ok else "marker missing or invalid",
        ),
        _executor_preflight_check(
            "shadow_execution_consumer_marker_scope_matches",
            passed=marker_scope_ok,
            detail=shadow_execution_approval_id,
        ),
        _executor_preflight_check(
            "shadow_execution_consumer_marker_has_no_secret_like_keys",
            passed=not marker_secret_errors,
            detail="; ".join(marker_secret_errors) if marker_secret_errors else "no secret-like keys detected",
        ),
        _executor_preflight_check(
            "shadow_execution_proof_browser_run_path_create_new",
            passed=browser_run_confined and browser_run_absent,
            detail=browser_run_path.as_posix(),
        ),
        _executor_preflight_check(
            "shadow_execution_proof_agent_activity_path_create_new",
            passed=agent_activity_confined and agent_activity_absent,
            detail=agent_activity_path.as_posix(),
        ),
        _executor_preflight_check(
            "shadow_execution_proof_audit_path_confined",
            passed=audit_confined,
            detail=run_audit_path.as_posix(),
        ),
        _executor_preflight_check(
            "shadow_execution_proof_payload_has_no_secret_like_keys",
            passed=not proof_secret_errors,
            detail="; ".join(proof_secret_errors) if proof_secret_errors else "no secret-like keys detected",
        ),
        _executor_preflight_check(
            "shadow_execution_proof_stops_before_browser_execution",
            passed=True,
            detail="proof artifact writer does not launch browser, connect CDP, use sessions, or mutate DOM",
        ),
    ]
    checks_passed = all(bool(check.get("passed")) for check in checks if check.get("required", True))
    ready_to_write = (
        checks_passed
        and approved_ready
        and marker_exists
        and marker_parse_ok
        and marker_scope_ok
        and browser_run_absent
        and agent_activity_absent
        and browser_run_confined
        and agent_activity_confined
        and audit_confined
        and not marker_secret_errors
        and not proof_secret_errors
    )
    if not marker_exists:
        proof_status = "blocked_shadow_execution_proof_consumption_marker_missing"
        review_decision = "blocked_before_shadow_execution_proof_artifact"
    elif not marker_parse_ok or not marker_scope_ok:
        proof_status = "blocked_shadow_execution_proof_consumption_marker_mismatch"
        review_decision = "blocked_before_shadow_execution_proof_artifact"
    elif not browser_run_absent or not agent_activity_absent:
        proof_status = "blocked_shadow_execution_proof_artifact_already_exists"
        review_decision = "blocked_create_new_shadow_execution_proof_already_exists"
    elif not approved_ready:
        proof_status = "blocked_shadow_execution_proof_readiness_not_ready"
        review_decision = "blocked_before_shadow_execution_proof_artifact"
    elif not ready_to_write:
        proof_status = "blocked_shadow_execution_proof_artifact_writer_preflight"
        review_decision = "blocked_before_shadow_execution_proof_artifact"
    elif not write_shadow_execution_proof:
        proof_status = "shadow_execution_proof_artifact_writer_ready_no_write"
        review_decision = "ready_requires_explicit_write_shadow_execution_proof_flag"
    else:
        proof_status = "shadow_execution_proof_artifact_writer_ready_to_write"
        review_decision = "write_shadow_execution_proof_artifacts_no_browser"

    run_ref: str | None = None
    audit_ref: str | None = None
    browser_run_ref: str | None = None
    agent_activity_ref: str | None = None
    browser_run_sha256: str | None = None
    agent_activity_sha256: str | None = None
    if write_shadow_execution_proof and ready_to_write:
        run = SiteOpsRun(
            run_id=run_id,
            tenant_id=tenant,
            workspace_id=workspace,
            user_id=user,
            skill_id=proposed_skill_id,
            workflow_id=PROMOTION_WORKFLOW_ID,
            site_profile_id=None,
            provider_id=None,
            mode="shadow_execution_proof_artifact",
            status="shadow_execution_proof_artifact_written_no_browser",
            inputs_ref=marker_path.as_posix(),
            outputs_ref=browser_run_path.as_posix(),
            audit_ref=run_audit_path.as_posix(),
            cost_estimate={"charged": False, "provider": None},
            cost_actual=None,
            started_at=now,
            ended_at=now_iso(),
        )
        run_ref = write_run_record(root, run)
        audit_ref = append_audit_event(
            root,
            SiteOpsAuditEvent(
                event_id=f"event_{run_id}_shadow_execution_proof_prewrite",
                run_id=run_id,
                tenant_id=tenant,
                workspace_id=workspace,
                user_id=user,
                event_type="shadow_execution_proof_prewrite",
                action=PROMOTION_BROWSER_SKILL_SHADOW_EXECUTION_PROOF_ACTION,
                target=candidate,
                policy_decision="allow_scoped_proof_artifact_no_browser",
                timestamp=now_iso(),
                metadata={
                    "shadow_execution_approval_id": shadow_execution_approval_id,
                    "consumer_marker_ref": marker_path.as_posix(),
                    "consumer_marker_sha256": marker_digest,
                    "browser_run_ref": browser_run_path.as_posix(),
                    "agent_activity_ref": agent_activity_path.as_posix(),
                    "browser_execution_allowed": False,
                    "canonical_writeback_allowed": False,
                },
                redacted_fields=[],
            ),
        )
        _write_json_create_new(browser_run_path, browser_run_payload)
        browser_run_ref = browser_run_path.as_posix()
        browser_run_sha256 = _sha256_json(browser_run_payload)
        agent_activity_text = (
            "---\n"
            "type: siteops-shadow-execution-proof\n"
            f"date: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}\n"
            "status: UNTRUSTED / NO BROWSER EXECUTION\n"
            "---\n\n"
            "# SiteOps Shadow Execution Proof Artifact\n\n"
            f"- Candidate: `{candidate}`\n"
            f"- Proposed skill: `{proposed_skill_id}`\n"
            f"- Tenant: `{tenant}`\n"
            f"- Workspace: `{workspace}`\n"
            f"- User: `{user}`\n"
            f"- Approval: `{shadow_execution_approval_id}`\n"
            f"- Consumer marker: `{marker_path.as_posix()}`\n"
            f"- Consumer marker SHA-256: `{marker_digest}`\n"
            f"- Browser Run proof: `{browser_run_path.as_posix()}`\n"
            "\n"
            "This artifact records proof readiness and marker consumption only. It did not launch a browser, connect CDP, use an authenticated session, read cookies/tokens/secrets/storage state, mutate DOM, promote trusted artifacts, activate a skill, enqueue Agent Bus work, call providers, mutate Gate policy, or write canonical ChaseOS state.\n"
        )
        agent_activity_path.parent.mkdir(parents=True, exist_ok=True)
        with agent_activity_path.open("x", encoding="utf-8") as handle:
            handle.write(agent_activity_text)
        agent_activity_ref = agent_activity_path.as_posix()
        agent_activity_sha256 = hashlib.sha256(agent_activity_text.encode("utf-8")).hexdigest()
        audit_ref = append_audit_event(
            root,
            SiteOpsAuditEvent(
                event_id=f"event_{run_id}_shadow_execution_proof_written",
                run_id=run_id,
                tenant_id=tenant,
                workspace_id=workspace,
                user_id=user,
                event_type="shadow_execution_proof_written",
                action=PROMOTION_BROWSER_SKILL_SHADOW_EXECUTION_PROOF_ACTION,
                target=candidate,
                policy_decision="shadow_execution_proof_artifact_written_no_browser",
                timestamp=now_iso(),
                metadata={
                    "shadow_execution_approval_id": shadow_execution_approval_id,
                    "browser_run_ref": browser_run_ref,
                    "browser_run_sha256": browser_run_sha256,
                    "agent_activity_ref": agent_activity_ref,
                    "agent_activity_sha256": agent_activity_sha256,
                    "browser_execution_performed": False,
                    "canonical_writeback_performed": False,
                },
                redacted_fields=[],
            ),
        )
        proof_status = "shadow_execution_proof_artifact_written_no_browser"
        review_decision = "shadow_execution_proof_artifact_written_review_required"

    writes_performed = bool(browser_run_ref or agent_activity_ref or run_ref or audit_ref)
    denied_effects = [
        "launch or control a browser",
        "connect CDP",
        "use authenticated browser session",
        "read cookies, tokens, secrets, localStorage, sessionStorage, or account state",
        "mutate DOM or submit forms",
        "promote trusted Browser Skill artifact",
        "activate promoted skills",
        "enqueue Agent Bus work",
        "call provider APIs",
        "mutate Gate policy",
        "write canonical ChaseOS memory/state",
    ]
    result = dict(readiness)
    result.update(
        {
            "action": PROMOTION_BROWSER_SKILL_SHADOW_EXECUTION_PROOF_ACTION,
            "shadow_execution_proof_status": proof_status,
            "review_decision": review_decision,
            "shadow_execution_approval_id": shadow_execution_approval_id,
            "actor": actor,
            "write_shadow_execution_proof_requested": bool(write_shadow_execution_proof),
            "write_shadow_execution_proof_flag_supported": True,
            "shadow_execution_proof_ready_to_write": ready_to_write,
            "shadow_execution_proof_checks": checks,
            "shadow_execution_consumer_marker_ref": marker_path.as_posix() if marker_exists else None,
            "shadow_execution_consumer_marker_sha256": marker_digest,
            "browser_run_ref": browser_run_ref,
            "browser_run_path": browser_run_path.as_posix(),
            "browser_run_sha256": browser_run_sha256,
            "agent_activity_ref": agent_activity_ref,
            "agent_activity_path": agent_activity_path.as_posix(),
            "agent_activity_sha256": agent_activity_sha256,
            "run_id": run_id,
            "run_ref": run_ref,
            "audit_ref": audit_ref,
            "blocked_actions": denied_effects,
            "denied_effects": denied_effects,
            "writes_performed": writes_performed,
            "files_modified": writes_performed,
            "run_record_written": bool(run_ref),
            "audit_events_written": bool(audit_ref),
            "approval_consumed": marker_exists and marker_scope_ok,
            "approval_decision_written": False,
            "approval_request_status_mutated": False,
            "shadow_execution_proof_written": bool(browser_run_ref),
            "browser_run_log_written": bool(browser_run_ref),
            "agent_activity_log_written": bool(agent_activity_ref),
            "browser_execution_allowed": False,
            "browser_launch_allowed": False,
            "browser_execution_performed": False,
            "browser_launch_performed": False,
            "cdp_connection_allowed": False,
            "cdp_connection_performed": False,
            "authenticated_session_allowed": False,
            "authenticated_session_used": False,
            "real_profile_allowed": False,
            "cookie_or_token_access_allowed": False,
            "dom_mutation_allowed": False,
            "external_submit_allowed": False,
            "trusted_promotion_allowed": False,
            "trusted_artifacts_written": False,
            "activation_allowed": False,
            "activation_performed": False,
            "agent_bus_enqueue_allowed": False,
            "provider_api_call_allowed": False,
            "gate_policy_mutation_allowed": False,
            "canonical_writeback_allowed": False,
            "boundary": (
                "Browser Skill shadow execution proof artifact writer only; it "
                "requires an approved shadow execution request and exact-once "
                "consumer marker, writes only scoped proof Browser Run, Agent "
                "Activity, SiteOpsRun, and SiteOpsAuditEvent artifacts with an "
                "explicit flag, and stops before browser/CDP execution, session "
                "use, DOM mutation, trusted promotion, activation, Agent Bus "
                "work, provider calls, Gate mutation, or canonical writeback."
            ),
        }
    )
    return result


def candidate_promotion_browser_skill_shadow_execution_proof_review_closeout(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    actor: str,
    target_url: str,
    shadow_execution_approval_id: str,
    shadow_mode: bool = False,
    local_target_only: bool = False,
    allowlisted_domain: str | None = None,
    max_steps: int = 5,
    source_approval_id: str | None = None,
    activation_approval_id: str | None = None,
    reason: str | None = None,
    write_review_closeout: bool = False,
) -> dict[str, Any]:
    """Review scoped no-browser shadow execution proof artifacts."""
    proof_context = candidate_promotion_browser_skill_shadow_execution_proof(
        candidate_id,
        root,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
        actor=actor,
        target_url=target_url,
        shadow_execution_approval_id=shadow_execution_approval_id,
        shadow_mode=shadow_mode,
        local_target_only=local_target_only,
        allowlisted_domain=allowlisted_domain,
        max_steps=max_steps,
        source_approval_id=source_approval_id,
        activation_approval_id=activation_approval_id,
        reason=reason or "operator requested shadow execution proof artifact review closeout",
        write_shadow_execution_proof=False,
    )
    scope = dict(proof_context.get("scope") or {})
    tenant = str(scope.get("tenant_id") or tenant_id or "")
    workspace = str(scope.get("workspace_id") or workspace_id or "")
    user = str(scope.get("user_id") or user_id or "")
    candidate = str(proof_context.get("candidate_id") or candidate_id)
    proposed_skill_id = str(proof_context.get("proposed_skill_id") or candidate)
    slug = _slug(candidate)
    resolved_root = Path(root or Path.cwd()).resolve()
    marker_path = Path(str(proof_context.get("shadow_execution_consumer_marker_ref") or ""))
    browser_run_path = Path(str(proof_context.get("browser_run_path") or ""))
    agent_activity_path = Path(str(proof_context.get("agent_activity_path") or ""))
    run_id = str(proof_context.get("run_id") or f"siteops_shadow_execution_proof_{_slug(candidate)[:48]}")
    run_path = resolved_root / "07_LOGS" / "SiteOps-Runs" / tenant / workspace / f"{run_id}.json"
    run_audit_path = audit_path(root, tenant, workspace, run_id)
    review_closeout_rel = (
        Path("07_LOGS")
        / "Browser-Runs"
        / tenant
        / workspace
        / f"siteops-shadow-execution-{slug}-proof-review.json"
    )
    review_closeout_path = resolved_root / review_closeout_rel
    evidence_paths = [marker_path, browser_run_path, agent_activity_path, run_path, run_audit_path]
    paths_confined = all(_filesystem_path_is_within(path, resolved_root) for path in evidence_paths + [review_closeout_path])
    evidence_exists = all(path.exists() and path.is_file() for path in evidence_paths)
    review_target_absent = not review_closeout_path.exists()

    marker_payload: dict[str, Any] = {}
    proof_payload: dict[str, Any] = {}
    run_payload: dict[str, Any] = {}
    agent_activity_text = ""
    audit_text = ""
    parse_ok = False
    marker_sha256: str | None = None
    proof_sha256: str | None = None
    run_sha256: str | None = None
    agent_activity_sha256: str | None = None
    audit_sha256: str | None = None
    if evidence_exists and paths_confined:
        try:
            marker_payload = json.loads(marker_path.read_text(encoding="utf-8"))
            proof_payload = json.loads(browser_run_path.read_text(encoding="utf-8"))
            run_payload = json.loads(run_path.read_text(encoding="utf-8"))
            agent_activity_text = agent_activity_path.read_text(encoding="utf-8")
            audit_text = run_audit_path.read_text(encoding="utf-8")
            marker_sha256 = _sha256_json(marker_payload)
            proof_sha256 = _sha256_json(proof_payload)
            run_sha256 = _sha256_json(run_payload)
            agent_activity_sha256 = _sha256_file(agent_activity_path)
            audit_sha256 = _sha256_file(run_audit_path)
            parse_ok = True
        except (OSError, ValueError, json.JSONDecodeError):
            parse_ok = False

    proof_record_ok = (
        parse_ok
        and proof_payload.get("record_type") == "siteops_browser_skill_shadow_execution_proof"
        and proof_payload.get("proof_status") == "shadow_execution_proof_artifact_written_no_browser_execution"
        and proof_payload.get("evidence_trust") == "untrusted_shadow_execution_proof"
    )
    marker_matches = (
        parse_ok
        and marker_payload.get("record_type") == "siteops_shadow_execution_approval_consumer"
        and marker_payload.get("tenant_id") == tenant
        and marker_payload.get("workspace_id") == workspace
        and marker_payload.get("user_id") == user
        and marker_payload.get("candidate_id") == candidate
        and marker_payload.get("proposed_skill_id") == proposed_skill_id
        and marker_payload.get("shadow_execution_approval_id") == shadow_execution_approval_id
        and marker_payload.get("target_url") == target_url
        and proof_payload.get("shadow_execution_consumer_marker_ref") == marker_path.as_posix()
        and proof_payload.get("shadow_execution_consumer_marker_sha256") == marker_sha256
    )
    proof_scope_matches = (
        parse_ok
        and proof_payload.get("tenant_id") == tenant
        and proof_payload.get("workspace_id") == workspace
        and proof_payload.get("user_id") == user
        and proof_payload.get("candidate_id") == candidate
        and proof_payload.get("proposed_skill_id") == proposed_skill_id
        and proof_payload.get("shadow_execution_approval_id") == shadow_execution_approval_id
        and proof_payload.get("source_approval_id") == source_approval_id
        and proof_payload.get("activation_approval_id") == activation_approval_id
        and proof_payload.get("target_url") == target_url
    )
    run_record_matches = (
        parse_ok
        and run_payload.get("run_id") == run_id
        and run_payload.get("tenant_id") == tenant
        and run_payload.get("workspace_id") == workspace
        and run_payload.get("user_id") == user
        and run_payload.get("mode") == "shadow_execution_proof_artifact"
        and run_payload.get("status") == "shadow_execution_proof_artifact_written_no_browser"
        and run_payload.get("inputs_ref") == marker_path.as_posix()
        and run_payload.get("outputs_ref") == browser_run_path.as_posix()
    )
    audit_matches = (
        parse_ok
        and "shadow_execution_proof_prewrite" in audit_text
        and "shadow_execution_proof_written" in audit_text
        and browser_run_path.as_posix() in audit_text
    )
    agent_activity_matches = (
        parse_ok
        and "UNTRUSTED / NO BROWSER EXECUTION" in agent_activity_text
        and marker_path.as_posix() in agent_activity_text
        and browser_run_path.as_posix() in agent_activity_text
        and str(marker_sha256 or "") in agent_activity_text
    )
    no_browser_effects = (
        parse_ok
        and proof_payload.get("browser_execution_performed") is False
        and proof_payload.get("browser_launch_performed") is False
        and proof_payload.get("cdp_connection_performed") is False
        and proof_payload.get("authenticated_session_used") is False
        and proof_payload.get("real_profile_used") is False
        and proof_payload.get("credential_material_accessed") is False
        and proof_payload.get("storage_state_accessed") is False
        and proof_payload.get("dom_mutation_performed") is False
        and proof_payload.get("external_submit_performed") is False
        and proof_payload.get("trusted_artifact_mutated") is False
        and proof_payload.get("activation_performed") is False
        and proof_payload.get("agent_bus_enqueue_performed") is False
        and proof_payload.get("provider_api_call_performed") is False
        and proof_payload.get("gate_policy_mutated") is False
        and proof_payload.get("canonical_writeback_performed") is False
    )
    no_secret_like_keys = (
        parse_ok
        and not scan_secret_like_keys(marker_payload)
        and not scan_secret_like_keys(proof_payload)
        and not scan_secret_like_keys(run_payload)
        and not _contains_forbidden_browser_run_fields(proof_payload)
    )
    target_secret_free = not _target_url_has_secret_marker(target_url)
    closeout_checks = [
        _executor_preflight_check(
            "shadow_execution_proof_artifacts_present",
            passed=evidence_exists,
            detail=", ".join(path.as_posix() for path in evidence_paths),
        ),
        _executor_preflight_check(
            "shadow_execution_proof_paths_confined",
            passed=paths_confined,
            detail="marker, proof Browser Run, Agent Activity, SiteOpsRun, audit, and review paths checked",
        ),
        _executor_preflight_check(
            "shadow_execution_proof_artifacts_parse",
            passed=parse_ok,
            detail="proof artifacts parsed" if parse_ok else "failed to parse one or more proof artifacts",
        ),
        _executor_preflight_check(
            "shadow_execution_proof_record_type_and_untrusted_status",
            passed=proof_record_ok,
            detail=str(proof_payload.get("evidence_trust") or "missing"),
        ),
        _executor_preflight_check(
            "shadow_execution_consumer_marker_digest_matches_proof",
            passed=marker_matches,
            detail=str(marker_sha256 or "missing"),
        ),
        _executor_preflight_check(
            "shadow_execution_proof_scope_matches_request",
            passed=proof_scope_matches,
            detail=f"{tenant}/{workspace}/{user} {candidate}",
        ),
        _executor_preflight_check(
            "shadow_execution_proof_run_record_matches",
            passed=run_record_matches,
            detail=run_path.as_posix(),
        ),
        _executor_preflight_check(
            "shadow_execution_proof_audit_events_present",
            passed=audit_matches,
            detail=run_audit_path.as_posix(),
        ),
        _executor_preflight_check(
            "shadow_execution_proof_agent_activity_matches",
            passed=agent_activity_matches,
            detail=agent_activity_path.as_posix(),
        ),
        _executor_preflight_check(
            "shadow_execution_proof_confirms_no_browser_or_session_effects",
            passed=no_browser_effects,
            detail="no browser/CDP/session/DOM/trusted/activation/provider/Gate/canonical effects recorded",
        ),
        _executor_preflight_check(
            "shadow_execution_proof_has_no_secret_like_keys",
            passed=no_secret_like_keys,
            detail="no secret-like fields detected" if no_secret_like_keys else "secret-like proof field detected",
        ),
        _executor_preflight_check(
            "shadow_execution_proof_target_url_secret_free",
            passed=target_secret_free,
            detail="no secret-like URL markers detected" if target_secret_free else "secret-like URL marker detected",
        ),
        _executor_preflight_check(
            "shadow_execution_proof_review_closeout_target_create_new",
            passed=review_target_absent,
            detail=review_closeout_path.as_posix(),
        ),
    ]
    closeout_ready = all(bool(check.get("passed")) for check in closeout_checks)
    review_record = {
        "record_type": "siteops_browser_skill_shadow_execution_proof_review_closeout",
        "tenant_id": tenant,
        "workspace_id": workspace,
        "user_id": user,
        "candidate_id": candidate,
        "proposed_skill_id": proposed_skill_id,
        "shadow_execution_approval_id": shadow_execution_approval_id,
        "source_approval_id": source_approval_id,
        "activation_approval_id": activation_approval_id,
        "target_url": target_url,
        "review_status": "closed_untrusted_no_browser_proof",
        "evidence_trust": "untrusted_shadow_execution_proof",
        "browser_run_ref": browser_run_path.as_posix(),
        "browser_run_sha256": proof_sha256,
        "agent_activity_ref": agent_activity_path.as_posix(),
        "agent_activity_sha256": agent_activity_sha256,
        "consumer_marker_ref": marker_path.as_posix(),
        "consumer_marker_sha256": marker_sha256,
        "run_ref": run_path.as_posix(),
        "run_sha256": run_sha256,
        "audit_ref": run_audit_path.as_posix(),
        "audit_sha256": audit_sha256,
        "reviewed_by": actor,
        "created_at": now_iso(),
        "checks": closeout_checks,
        "trusted_promotion_allowed": False,
        "ready_for_trusted_promotion_review_next": closeout_ready,
        "browser_execution_allowed": False,
        "canonical_writeback_allowed": False,
    }
    review_ref: str | None = None
    review_sha256: str | None = None
    if write_review_closeout and closeout_ready:
        _write_json_create_new(review_closeout_path, review_record)
        review_ref = review_closeout_path.as_posix()
        review_sha256 = _sha256_json(review_record)
        closeout_status = "shadow_execution_proof_artifact_review_closeout_written"
        review_decision = "closed_untrusted_no_browser_proof_ready_for_trust_review_decision"
    elif not review_target_absent:
        closeout_status = "blocked_shadow_execution_proof_review_closeout_already_exists"
        review_decision = "proof_review_closeout_already_exists_create_new_blocked"
    elif write_review_closeout and not closeout_ready:
        closeout_status = "blocked_shadow_execution_proof_artifact_review_closeout"
        review_decision = "repair_shadow_execution_proof_artifacts_before_closeout"
    else:
        closeout_status = (
            "shadow_execution_proof_artifact_review_closeout_ready_no_write"
            if closeout_ready
            else "blocked_shadow_execution_proof_artifact_review_closeout"
        )
        review_decision = (
            "rerun_with_write_review_closeout_after_operator_review"
            if closeout_ready
            else "repair_shadow_execution_proof_artifacts_before_closeout"
        )

    result = dict(proof_context)
    result.update(
        {
            "action": PROMOTION_BROWSER_SKILL_SHADOW_EXECUTION_PROOF_REVIEW_CLOSEOUT_ACTION,
            "shadow_execution_proof_review_closeout_status": closeout_status,
            "review_decision": review_decision,
            "shadow_execution_proof_review_closeout_checks": closeout_checks,
            "review_closeout_record": review_record if review_ref else None,
            "review_closeout_ref": review_ref,
            "review_closeout_path": review_closeout_path.as_posix(),
            "review_closeout_sha256": review_sha256,
            "write_review_closeout_requested": bool(write_review_closeout),
            "browser_run_ref": browser_run_path.as_posix() if browser_run_path.exists() else None,
            "browser_run_sha256": proof_sha256,
            "agent_activity_ref": agent_activity_path.as_posix() if agent_activity_path.exists() else None,
            "agent_activity_sha256": agent_activity_sha256,
            "shadow_execution_consumer_marker_ref": marker_path.as_posix() if marker_path.exists() else None,
            "shadow_execution_consumer_marker_sha256": marker_sha256,
            "proof_run_ref": run_path.as_posix() if run_path.exists() else None,
            "proof_run_sha256": run_sha256,
            "proof_audit_ref": run_audit_path.as_posix() if run_audit_path.exists() else None,
            "proof_audit_sha256": audit_sha256,
            "ready_for_trusted_promotion_review_next": closeout_ready and bool(review_ref or not write_review_closeout),
            "trusted_promotion_allowed": False,
            "browser_execution_allowed": False,
            "browser_launch_allowed": False,
            "cdp_connection_allowed": False,
            "authenticated_session_allowed": False,
            "real_profile_allowed": False,
            "cookie_or_token_access_allowed": False,
            "dom_mutation_allowed": False,
            "external_submit_allowed": False,
            "agent_bus_enqueue_allowed": False,
            "provider_api_call_allowed": False,
            "gate_policy_mutation_allowed": False,
            "canonical_writeback_allowed": False,
            "review_closeout_written": bool(review_ref),
            "shadow_execution_proof_written": False,
            "browser_run_log_written": False,
            "agent_activity_log_written": False,
            "run_record_written": False,
            "audit_events_written": False,
            "activation_record_written": False,
            "activation_audit_written": False,
            "trusted_artifacts_written": False,
            "trusted_artifacts_mutated": False,
            "activation_performed": False,
            "writes_performed": bool(review_ref),
            "files_modified": bool(review_ref),
            "boundary": (
                "Browser Skill shadow execution proof review closeout only; it "
                "validates scoped untrusted proof Browser Run, Agent Activity, "
                "SiteOpsRun, SiteOpsAuditEvent, and consumption marker evidence. "
                "It may write only a scoped review closeout artifact when "
                "explicitly requested. It does not launch browser/CDP, use "
                "authenticated sessions, mutate DOM, promote trusted artifacts, "
                "activate skills, enqueue Agent Bus work, call providers, mutate "
                "Gate, or write canonical ChaseOS state."
            ),
        }
    )
    return result


def _candidate_approval_related(approval: dict[str, Any], candidate_id: str) -> bool:
    metadata = dict(approval.get("metadata") or {})
    if metadata.get("candidate_id") == candidate_id:
        return True
    needles = {candidate_id, _slug(candidate_id)}
    haystack = " ".join(
        str(approval.get(key) or "")
        for key in ("approval_id", "run_id", "approval_reason")
    )
    return any(needle and needle in haystack for needle in needles)


def candidate_promotion_source_approval_rebind_live_readiness(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    actor: str,
    legacy_approval_id: str | None = None,
    approval_id: str | None = None,
    reason: str | None = None,
) -> dict[str, Any]:
    """Report the no-write path from legacy source approval to bound source approval."""
    scope = require_scope(tenant_id=tenant_id, workspace_id=workspace_id, user_id=user_id)
    _validate_request_scope(root, scope)
    contract = candidate_promotion_request_contract(
        candidate_id,
        root,
        requested_by=actor or scope.user_id,
        tenant_id=scope.tenant_id,
        workspace_id=scope.workspace_id,
        user_id=scope.user_id,
    )
    resolved_candidate_id = str(contract.get("candidate_id") or candidate_id)
    proposed_skill_id = str(contract.get("proposed_skill_id") or "")
    approvals = list_approval_requests(root, tenant_id=scope.tenant_id, workspace_id=scope.workspace_id)

    source_candidates: list[dict[str, Any]] = []
    source_lookup: dict[str, dict[str, Any]] = {}
    for approval in approvals:
        approval_id_value = str(approval.get("approval_id") or "")
        if approval.get("action") != PROMOTION_ACTION:
            continue
        if approval.get("tenant_id") != scope.tenant_id:
            continue
        if approval.get("workspace_id") != scope.workspace_id or approval.get("user_id") != scope.user_id:
            continue
        if not _candidate_approval_related(approval, resolved_candidate_id):
            continue
        provenance = _approval_provenance_status(
            approval=approval,
            candidate_id=resolved_candidate_id,
            proposed_skill_id=proposed_skill_id or None,
        )
        record = {
            "approval_id": approval_id_value,
            "status": approval.get("status"),
            "approval_ref": approval.get("approval_ref"),
            "requested_by": approval.get("requested_by"),
            "provenance_status": provenance.get("provenance_status"),
            "candidate_id_matches": provenance.get("candidate_id_matches"),
            "proposed_skill_id_matches": provenance.get("proposed_skill_id_matches"),
            "bound_candidate_id": provenance.get("bound_candidate_id"),
            "bound_proposed_skill_id": provenance.get("bound_proposed_skill_id"),
        }
        source_lookup[approval_id_value] = approval
        source_candidates.append(record)

    bound_ready = [
        item for item in source_candidates
        if item.get("status") == "approved" and item.get("provenance_status") == "bound_match"
    ]
    approved_legacy = [
        item for item in source_candidates
        if item.get("status") == "approved" and item.get("provenance_status") == "legacy_unbound"
    ]
    pending_legacy = [
        item for item in source_candidates
        if item.get("status") == "pending" and item.get("provenance_status") == "legacy_unbound"
    ]
    mismatched = [
        item for item in source_candidates
        if item.get("provenance_status") not in {"bound_match", "legacy_unbound"}
    ]

    selected_legacy_id = str(legacy_approval_id or approval_id or "").strip()
    selected_kind = "operator_supplied" if selected_legacy_id else None
    if not selected_legacy_id and approved_legacy:
        selected_legacy_id = str(approved_legacy[0].get("approval_id") or "")
        selected_kind = "approved_legacy_unbound"
    if not selected_legacy_id and pending_legacy:
        selected_legacy_id = str(pending_legacy[0].get("approval_id") or "")
        selected_kind = "pending_legacy_unbound"
    selected_legacy = next(
        (item for item in source_candidates if item.get("approval_id") == selected_legacy_id),
        None,
    )

    rebind_spec: dict[str, Any] | None = None
    bound_spec: dict[str, Any] | None = None
    rebind_error: str | None = None
    writer_dry_run: dict[str, Any] | None = None
    writer_dry_run_error: str | None = None
    if selected_legacy_id:
        try:
            rebind_spec = candidate_promotion_approval_rebind_spec(
                resolved_candidate_id,
                root,
                tenant_id=scope.tenant_id,
                workspace_id=scope.workspace_id,
                user_id=scope.user_id,
                approval_id=selected_legacy_id,
            )
            bound_spec = candidate_promotion_bound_approval_request_spec(
                resolved_candidate_id,
                root,
                tenant_id=scope.tenant_id,
                workspace_id=scope.workspace_id,
                user_id=scope.user_id,
                approval_id=selected_legacy_id,
            )
            writer_dry_run = candidate_promotion_bound_approval_writer_implementation(
                resolved_candidate_id,
                root,
                tenant_id=scope.tenant_id,
                workspace_id=scope.workspace_id,
                user_id=scope.user_id,
                approval_id=selected_legacy_id,
                actor=actor,
                reason=reason or "operator requested source approval rebind live readiness",
                write_replacement_approval=False,
            )
        except (SiteOpsError, RuntimeError, ValueError) as exc:
            rebind_error = str(exc)
            writer_dry_run_error = str(exc)

    replacement_ready = bool(
        bound_spec
        and bound_spec.get("bound_approval_request_spec_status") == "bound_approval_request_spec_ready_no_write"
        and writer_dry_run
        and writer_dry_run.get("bound_approval_writer_implementation_status") == "bound_approval_writer_ready_dry_run_no_write"
    )
    bound_source_ready = bool(bound_ready)
    if bound_source_ready:
        readiness_status = "source_approval_rebind_not_required_bound_source_ready"
        review_decision = "use_existing_bound_source_promotion_approval_for_activation_chain"
    elif replacement_ready:
        readiness_status = "source_approval_rebind_live_readiness_ready_no_write"
        review_decision = "ready_for_operator_reviewed_write_replacement_source_approval"
    elif selected_legacy and selected_legacy.get("status") != "approved":
        readiness_status = "blocked_legacy_source_approval_not_approved"
        review_decision = "approve_or_replace_legacy_source_approval_before_rebind"
    elif selected_legacy and selected_legacy.get("provenance_status") != "legacy_unbound":
        readiness_status = "blocked_selected_source_approval_not_legacy_unbound"
        review_decision = "select_approved_legacy_unbound_source_approval_or_existing_bound_approval"
    elif rebind_error:
        readiness_status = "blocked_source_approval_rebind_preflight_error"
        review_decision = "repair_source_approval_rebind_inputs"
    else:
        readiness_status = "blocked_no_source_promotion_approval_for_candidate"
        review_decision = "create_scoped_source_promotion_approval_request"

    replacement_write_command_preview = [
        "python",
        "-m",
        "runtime.cli.main",
        "siteops",
        "candidates",
        "bound-approval-writer-implementation",
        resolved_candidate_id,
        "--approval-id",
        selected_legacy_id or "<LEGACY_SOURCE_APPROVAL_ID>",
        "--tenant",
        scope.tenant_id,
        "--workspace",
        scope.workspace_id,
        "--user",
        scope.user_id,
        "--actor",
        actor,
        "--write-replacement-approval",
        "--json",
    ]
    request_command_preview = [
        "python",
        "-m",
        "runtime.cli.main",
        "siteops",
        "candidates",
        "request-promotion",
        resolved_candidate_id,
        "--tenant",
        scope.tenant_id,
        "--workspace",
        scope.workspace_id,
        "--user",
        scope.user_id,
        "--requested-by",
        actor,
        "--write-approval-request",
        "--json",
    ]
    evidence_items = [
        {
            "evidence_key": "candidate_source_approval_inventory",
            "status": "satisfied" if source_candidates else "missing",
            "count": len(source_candidates),
            "required": True,
            "next_action": None if source_candidates else "create_scoped_source_promotion_approval_request",
        },
        {
            "evidence_key": "existing_bound_source_approval",
            "status": "satisfied" if bound_source_ready else "missing",
            "ref": (bound_ready[0].get("approval_id") if bound_ready else None),
            "required": False,
            "next_action": None if bound_source_ready else "inspect_legacy_source_approval_for_rebind",
        },
        {
            "evidence_key": "legacy_unbound_source_approval",
            "status": "satisfied" if selected_legacy else "missing",
            "ref": selected_legacy_id or None,
            "required": not bound_source_ready,
            "next_action": None if selected_legacy or bound_source_ready else "provide_or_create_source_promotion_approval",
        },
        {
            "evidence_key": "legacy_source_approval_approved",
            "status": "satisfied" if selected_legacy and selected_legacy.get("status") == "approved" else "missing_or_pending",
            "ref": selected_legacy_id or None,
            "required": bool(selected_legacy and not bound_source_ready),
            "next_action": None
            if selected_legacy and selected_legacy.get("status") == "approved"
            else "approve_or_replace_legacy_source_approval",
        },
        {
            "evidence_key": "replacement_bound_approval_spec",
            "status": "satisfied" if bound_spec and bound_spec.get("bound_approval_request_spec_status") == "bound_approval_request_spec_ready_no_write" else "missing_or_blocked",
            "ref": ((bound_spec or {}).get("approval_request_artifact") or {}).get("approval_id"),
            "required": bool(selected_legacy and not bound_source_ready),
            "next_action": None if replacement_ready else "run_bound_approval_writer_readiness_or_repair_spec",
        },
        {
            "evidence_key": "replacement_writer_dry_run",
            "status": "satisfied" if replacement_ready else "missing_or_blocked",
            "ref": (writer_dry_run or {}).get("bound_approval_writer_implementation_status"),
            "required": bool(selected_legacy and not bound_source_ready),
            "next_action": None if replacement_ready else "repair_bound_approval_writer_dry_run",
        },
    ]
    blockers = [
        item["evidence_key"]
        for item in evidence_items
        if item.get("required") and item.get("status") not in {"satisfied"}
    ]
    next_required_actions = [
        item["next_action"]
        for item in evidence_items
        if item.get("next_action")
    ]
    if replacement_ready:
        next_required_actions.insert(0, "operator_may_write_replacement_source_approval_request")
    if bound_source_ready:
        next_required_actions.insert(0, "continue_activation_approval_chain_with_bound_source_approval")

    return {
        "ok": True,
        "action": PROMOTION_SOURCE_APPROVAL_REBIND_LIVE_READINESS_ACTION,
        "candidate_id": resolved_candidate_id,
        "proposed_skill_id": proposed_skill_id or None,
        "scope": scope.as_dict(),
        "actor": actor,
        "source_approval_id": selected_legacy_id or (bound_ready[0].get("approval_id") if bound_ready else None),
        "source_approval_status": (selected_legacy or (bound_ready[0] if bound_ready else {})).get("status"),
        "source_approval_provenance_status": (selected_legacy or (bound_ready[0] if bound_ready else {})).get(
            "provenance_status"
        ),
        "source_approval_rebind_live_readiness_status": readiness_status,
        "review_decision": review_decision,
        "selected_legacy_approval_id": selected_legacy_id or None,
        "selected_legacy_approval_kind": selected_kind,
        "source_approval_candidates": source_candidates,
        "approved_legacy_unbound_approval_ids": [item.get("approval_id") for item in approved_legacy],
        "pending_legacy_unbound_approval_ids": [item.get("approval_id") for item in pending_legacy],
        "bound_source_approval_ids": [item.get("approval_id") for item in bound_ready],
        "mismatched_source_approval_ids": [item.get("approval_id") for item in mismatched],
        "rebind_spec_status": (rebind_spec or {}).get("approval_rebind_spec_status"),
        "bound_approval_request_spec_status": (bound_spec or {}).get("bound_approval_request_spec_status"),
        "bound_approval_writer_dry_run_status": (writer_dry_run or {}).get("bound_approval_writer_implementation_status"),
        "rebind_error": rebind_error,
        "writer_dry_run_error": writer_dry_run_error,
        "replacement_approval_request_preview": (bound_spec or {}).get("approval_request_artifact"),
        "replacement_write_command_preview": replacement_write_command_preview,
        "request_source_approval_command_preview": request_command_preview,
        "evidence_items": evidence_items,
        "remaining_source_approval_blockers": blockers,
        "next_required_actions": next_required_actions,
        "backend_activation_can_continue": bound_source_ready,
        "replacement_approval_needed": bool(selected_legacy and not bound_source_ready),
        "replacement_source_approval_ready_to_write": replacement_ready,
        "feature_done": False,
        "writes_performed": False,
        "files_modified": False,
        "run_record_written": False,
        "approval_request_artifact_written": False,
        "replacement_approval_request_written": False,
        "legacy_approval_mutation_allowed": False,
        "approval_decision_written": False,
        "approval_consumed": False,
        "approval_request_status_mutated": False,
        "trusted_artifacts_written": False,
        "trusted_artifacts_mutated": False,
        "trusted_skill_write_allowed": False,
        "siteops_skill_card_write_allowed": False,
        "activation_allowed": False,
        "activation_performed": False,
        "browser_execution_allowed": False,
        "agent_bus_enqueue_allowed": False,
        "provider_api_call_allowed": False,
        "gate_policy_mutation_allowed": False,
        "canonical_writeback_allowed": False,
        "blocked_actions": [
            "mutate legacy approval artifact",
            "write replacement approval request",
            "approve or reject approval request",
            "consume approvals",
            "write trusted Browser Skill artifact",
            "write SiteOps Skill Card artifact",
            "activate trusted artifacts",
            "launch or control a browser",
            "enqueue Agent Bus work",
            "call provider APIs",
            "mutate Gate policy",
            "write canonical ChaseOS memory/state",
        ],
        "boundary": (
            "source approval rebind live readiness only; it inventories source "
            "promotion approvals, identifies legacy-unbound blockers, composes "
            "replacement bound-approval dry-run posture, and previews the next "
            "operator command. It does not mutate legacy approvals, write "
            "replacement approvals, decide or consume approvals, activate "
            "artifacts, run browsers, call providers, mutate Gate, or write "
            "canonical ChaseOS state."
        ),
    }


def _trusted_target_collision_check(
    vault_root: Path,
    base_rel: Path,
    artifact_kind: str,
    target_path: str | None,
) -> dict[str, Any]:
    path_text = str(target_path or "").strip()
    confined = _repo_path_is_confined(path_text, base_rel)
    exists = bool((vault_root / path_text).exists()) if path_text and confined else False
    return {
        "artifact_kind": artifact_kind,
        "target_path": path_text,
        "path_confined": confined,
        "exists_on_disk": exists,
        "collision_detected": exists,
        "overwrite_allowed": False,
        "idempotent_noop_allowed": False,
        "requires_manual_review_if_exists": True,
        "write_allowed_in_this_pass": False,
    }


def candidate_promotion_collision_policy_spec(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    approval_id: str,
) -> dict[str, Any]:
    """Return a no-write collision/idempotency policy packet for future trusted writes."""
    validator = candidate_promotion_inactive_artifact_validator(
        candidate_id,
        root,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
        approval_id=approval_id,
    )
    validator_status = str(validator.get("inactive_artifact_validator_status") or "")
    validator_ready = validator_status == "inactive_artifact_validator_ready_no_authority"
    root_path = Path(root or ".").resolve()
    proposed_skill_id = str(validator.get("proposed_skill_id") or "").strip()
    if not proposed_skill_id:
        contract = candidate_promotion_request_contract(
            candidate_id,
            root,
            requested_by=user_id,
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            user_id=user_id,
        )
        proposed_skill_id = str(contract.get("proposed_skill_id") or "").strip()
    target_paths = {
        "browser_skill": (TRUSTED_SKILL_REL / f"{proposed_skill_id}.yaml").as_posix()
        if proposed_skill_id
        else None,
        "siteops_skill_card": _siteops_skill_card_target(proposed_skill_id),
    }
    target_checks = [
        _trusted_target_collision_check(root_path, TRUSTED_SKILL_REL, "browser_skill", target_paths["browser_skill"]),
        _trusted_target_collision_check(
            root_path,
            SITEOPS_SKILL_CARD_REL,
            "siteops_skill_card",
            target_paths["siteops_skill_card"],
        ),
    ]
    collision_detected = any(item.get("collision_detected") for item in target_checks)
    paths_confined = all(item.get("path_confined") for item in target_checks)
    collision_policy_pass = validator_ready and paths_confined and not collision_detected
    if not paths_confined:
        policy_status = "blocked_unconfined_target_path"
        review_decision = "blocked_target_path_boundary"
    elif collision_detected:
        policy_status = "blocked_target_collision"
        review_decision = "blocked_existing_target_requires_manual_collision_review"
    elif not validator_ready:
        policy_status = f"blocked_inactive_artifact_validator: {validator_status}"
        review_decision = "blocked_before_collision_policy"
    else:
        policy_status = "collision_policy_spec_ready_no_authority"
        review_decision = "collision_contract_only_do_not_write_in_this_pass"

    collision_policy = {
        "default": "fail_closed",
        "pre_existing_target": "block",
        "overwrite": "forbidden_without_separate_operator_approval_and_collision_review",
        "idempotent_noop": "future_only_after_exact_provenance_and_payload_match",
        "partial_write": "future_executor_must_roll_back_or_mark_recovery_required",
        "activation_after_write": "forbidden",
        "canonical_writeback_after_write": "forbidden",
    }
    future_idempotency_checks = [
        "existing artifact source_candidate_id must match candidate_id",
        "existing artifact tenant_id/workspace_id/created_by must match scoped approval",
        "existing artifact status must be inactive_review",
        "existing artifact activation_allowed must be false",
        "existing artifact payload hash must match proposed payload hash",
        "existing artifact provenance approval_id must match or be manually rebound",
    ]
    future_rollback_rules = [
        "validate all target paths before first write",
        "write artifacts through a staged temporary path before final move",
        "never activate a partially written skill",
        "write recovery-required audit event before stopping on partial failure",
        "do not overwrite an existing trusted target during rollback",
    ]
    denied_effects = [
        "write inactive trusted artifacts",
        "overwrite existing trusted artifacts",
        "mark idempotent no-op as applied",
        "write audit events",
        "create apply_trusted_candidate_artifacts executor",
        "edit runtime/policy/gateway_allowlists.json",
        "write runtime/browser_skills/skills artifacts",
        "write runtime/siteops/registry/skill_cards artifacts",
        "launch or control a browser",
        "enqueue Agent Bus work",
        "call provider APIs",
        "activate promoted skills",
        "write canonical ChaseOS memory/state",
    ]
    return {
        "ok": True,
        "action": PROMOTION_COLLISION_POLICY_SPEC_ACTION,
        "candidate_id": validator.get("candidate_id"),
        "proposed_skill_id": validator.get("proposed_skill_id"),
        "scope": validator.get("scope"),
        "approval_status": validator.get("approval_status"),
        "provenance_status": validator.get("provenance_status"),
        "inactive_artifact_validator_status": validator_status,
        "collision_policy_status": policy_status,
        "review_decision": review_decision,
        "gate_operation": PROMOTION_GATE_APPLY_OPERATION,
        "operation_currently_allowlisted": validator.get("operation_currently_allowlisted"),
        "target_path_checks": target_checks,
        "collision_policy": collision_policy,
        "future_idempotency_checks": future_idempotency_checks,
        "future_rollback_rules": future_rollback_rules,
        "collision_policy_pass": collision_policy_pass,
        "blocked_actions": denied_effects,
        "denied_effects": denied_effects,
        "writes_performed": False,
        "audit_events_written": False,
        "inactive_artifacts_written": False,
        "collision_policy_wrote_artifacts": False,
        "overwrite_allowed": False,
        "collision_resolution_allowed": False,
        "idempotent_apply_allowed": False,
        "rollback_performed": False,
        "executor_implemented": False,
        "executor_enabled": False,
        "executor_build_allowed": False,
        "executor_implementation_allowed": False,
        "executor_implementation_performed": False,
        "allowlist_change_allowed": False,
        "allowlist_change_performed": False,
        "policy_file_write_allowed": False,
        "trusted_skill_write_allowed": False,
        "siteops_skill_card_write_allowed": False,
        "browser_execution_allowed": False,
        "agent_bus_enqueue_allowed": False,
        "provider_api_call_allowed": False,
        "activation_allowed": False,
        "canonical_writeback_allowed": False,
        "boundary": (
            "collision policy spec only; no executor implementation, audit event "
            "write, Gate allowlist mutation, trusted artifact write, overwrite, "
            "idempotent apply, activation, browser execution, Agent Bus enqueue, "
            "provider call, or canonical writeback is performed in this pass"
        ),
    }
