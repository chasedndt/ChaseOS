"""CLI handlers for the ChaseOS SiteOps dry-run registry."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from typing import Any

from runtime.browser_skills.candidates import (
    BrowserSkillCandidateError,
    candidate_promotion_request_contract,
    list_candidate_records,
    preflight_candidate_promotion,
    show_candidate_record,
    storage_reconciliation,
)
from runtime.siteops.approvals import (
    decide_approval_request,
    list_approval_requests,
    show_approval_request,
)
from runtime.siteops.audit import list_run_records, show_run_record
from runtime.siteops.browser_profiles import check_browser_profile_ref, list_browser_profile_refs
from runtime.siteops.budgets import check_budget_policy, list_budget_policies
from runtime.siteops.candidate_promotions import (
    apply_trusted_candidate_artifacts,
    candidate_promotion_activation_approval_decision_consumer_design,
    candidate_promotion_activation_approval_decision_consumer_write_guard_contract,
    candidate_promotion_activation_approval_decision_consumer_writer_design,
    candidate_promotion_activation_approval_decision_consumer_writer_implementation,
    candidate_promotion_activation_approval_decision_consumer_writer_implementation_approval,
    candidate_promotion_activation_approval_decision_consumer_writer_implementation_request,
    candidate_promotion_activation_consumption_live_readiness,
    candidate_promotion_activation_executor_design,
    candidate_promotion_activation_executor_implementation,
    candidate_promotion_activation_executor_implementation_approval,
    candidate_promotion_activation_executor_implementation_request,
    candidate_promotion_activation_gate_live_readiness,
    candidate_promotion_activation_gate_policy_patch_writer_implementation,
    candidate_promotion_activation_executor_live_readiness,
    candidate_promotion_activation_executor_preflight,
    candidate_promotion_activation_approval_decision_preflight,
    candidate_promotion_activation_approval_request,
    candidate_promotion_activation_boundary_readiness,
    candidate_promotion_apply_contract,
    candidate_promotion_approval_rebind_spec,
    candidate_promotion_bound_approval_request_spec,
    candidate_promotion_bound_approval_writer_design,
    candidate_promotion_bound_approval_writer_implementation,
    candidate_promotion_bound_approval_writer_implementation_approval,
    candidate_promotion_bound_approval_writer_implementation_request,
    candidate_promotion_bound_approval_writer_preflight,
    candidate_promotion_browser_skill_shadow_replay_design,
    candidate_promotion_browser_skill_shadow_replay_implementation_approval,
    candidate_promotion_browser_skill_shadow_replay_implementation_request,
    candidate_promotion_browser_skill_shadow_replay_evidence_review_closeout,
    candidate_promotion_browser_skill_shadow_execution_approval_packet,
    candidate_promotion_browser_skill_shadow_execution_approval_decision_preflight,
    candidate_promotion_browser_skill_shadow_execution_approval_decision_request,
    candidate_promotion_browser_skill_shadow_execution_approval_live_decision_readiness,
    candidate_promotion_browser_skill_shadow_execution_proof,
    candidate_promotion_browser_skill_shadow_execution_proof_review_closeout,
    candidate_promotion_browser_skill_shadow_execution_proof_consumption_guard,
    candidate_promotion_browser_skill_shadow_execution_proof_readiness,
    candidate_promotion_browser_skill_shadow_replay_runner_implementation_dry_run,
    candidate_promotion_browser_skill_shadow_replay_runner_write_pass,
    candidate_promotion_browser_skill_shadow_replay_runner_write_guard,
    candidate_promotion_live_activation_evidence_closeout,
    candidate_promotion_source_approval_rebind_live_readiness,
    candidate_promotion_replacement_approval_decision_consumption,
    candidate_promotion_collision_policy_spec,
    candidate_promotion_executor_implementation_design_review,
    candidate_promotion_executor_prewrite_audit_spec,
    candidate_promotion_executor_review_checklist,
    candidate_promotion_gate_apply_design,
    candidate_promotion_gate_allowlist_review,
    candidate_promotion_gate_executor_spec,
    candidate_promotion_preimplementation_verifier,
    candidate_promotion_inactive_artifact_validator,
    candidate_promotion_trusted_inactive_artifact_writer_implementation_approval,
    candidate_promotion_trusted_inactive_artifact_writer_implementation,
    candidate_promotion_trusted_inactive_artifact_writer_gate_allowlist_approval_request,
    candidate_promotion_trusted_inactive_artifact_writer_gate_allowlist_decision_preflight,
    candidate_promotion_trusted_inactive_artifact_writer_gate_policy_patch_application_design,
    candidate_promotion_trusted_inactive_artifact_writer_gate_policy_patch_application_preflight,
    candidate_promotion_trusted_inactive_artifact_writer_gate_policy_patch_application_write_guard_contract,
    candidate_promotion_trusted_inactive_artifact_writer_gate_policy_patch_writer_design,
    candidate_promotion_trusted_inactive_artifact_writer_gate_policy_patch_writer_implementation,
    candidate_promotion_trusted_inactive_artifact_writer_gate_policy_patch_writer_implementation_approval,
    candidate_promotion_trusted_inactive_artifact_writer_gate_policy_patch_writer_implementation_request,
    candidate_promotion_trusted_inactive_artifact_writer_gate_policy_live_application_readiness,
    candidate_promotion_trusted_inactive_artifact_writer_gate_policy_patch_plan,
    candidate_promotion_trusted_inactive_artifact_writer_live_gate_readiness,
    candidate_promotion_trusted_inactive_artifact_writer_implementation_request,
    candidate_promotion_trusted_inactive_artifact_writer_preflight,
    candidate_promotion_trusted_executor_design,
    list_candidate_promotion_approvals,
    request_scoped_candidate_promotion,
)
from runtime.siteops.credentials import check_credential_ref, list_credential_refs
from runtime.siteops.registry import (
    SiteOpsRegistryError,
    build_dry_run_plan,
    load_registry,
    parse_cli_inputs,
    show_object,
    validate_registry,
)
from runtime.siteops.errors import SiteOpsError
from runtime.siteops.runner import run_siteops_dry_run, run_siteops_live
from runtime.siteops.tenancy import (
    DEFAULT_LOCAL_SCOPE,
    list_tenants,
    load_catalog,
    load_tenant,
    objects_by_id,
    save_tenant,
)
from runtime.siteops.validator import validate_production_siteops


def _print_json_or_text(args: argparse.Namespace, payload: dict[str, Any], lines: list[str]) -> int:
    if getattr(args, "output_json", False):
        print(json.dumps(payload, indent=2))
        return 0 if payload.get("ok", True) else 1
    print("\n".join(lines))
    return 0 if payload.get("ok", True) else 1


def _error(args: argparse.Namespace, exc: Exception) -> int:
    payload = {"ok": False, "reason": str(exc)}
    if getattr(args, "output_json", False):
        print(json.dumps(payload, indent=2))
    else:
        print(f"ERROR: {exc}")
    return 1


def _vault_root_arg(args: argparse.Namespace) -> str | None:
    return getattr(args, "vault_root", None)


def _tenant_arg(args: argparse.Namespace) -> str:
    return getattr(args, "tenant_id", None) or DEFAULT_LOCAL_SCOPE["tenant_id"]


def _workspace_arg(args: argparse.Namespace) -> str:
    return getattr(args, "workspace_id", None) or DEFAULT_LOCAL_SCOPE["workspace_id"]


def _user_arg(args: argparse.Namespace) -> str:
    return getattr(args, "user_id", None) or DEFAULT_LOCAL_SCOPE["user_id"]


def _slug(value: str) -> str:
    clean = "".join(ch.lower() if ch.isalnum() else "-" for ch in value)
    return "-".join(part for part in clean.split("-") if part) or "siteops"


def _scope_lines(payload: dict[str, Any]) -> list[str]:
    scope = payload.get("scope") or {}
    return [
        f"  tenant_id: {scope.get('tenant_id')}",
        f"  workspace_id: {scope.get('workspace_id')}",
        f"  user_id: {scope.get('user_id')}",
    ]


def cmd_siteops_list(args: argparse.Namespace) -> int:
    try:
        registry = load_registry(getattr(args, "vault_root", None))
    except SiteOpsRegistryError as exc:
        print(f"ERROR: {exc}")
        return 1

    kind_filter = getattr(args, "object_type", "all")
    kinds = [kind_filter] if kind_filter != "all" else ["site", "provider", "workflow", "skill"]
    items: list[dict[str, Any]] = []
    for kind in kinds:
        for obj in registry.get(kind, []):
            data = obj.data
            items.append(
                {
                    "id": obj.object_id,
                    "type": kind,
                    "display_name": data.get("display_name"),
                    "status": data.get("status"),
                    "execution_status": data.get("execution_status") or data.get("profile_status"),
                    "path": str(obj.path),
                }
            )

    payload = {
        "ok": True,
        "object_type": kind_filter,
        "count": len(items),
        "items": items,
    }
    lines = ["ChaseOS SiteOps Registry", f"  object_type: {kind_filter}", f"  count: {len(items)}"]
    for item in items:
        lines.append(f"  - {item['type']}: {item['id']} ({item.get('status')})")
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_show(args: argparse.Namespace) -> int:
    try:
        object_type = getattr(args, "object_type", None)
        if object_type:
            payload = show_object(
                args.object_id,
                vault_root=getattr(args, "vault_root", None),
                object_type=object_type,
            )
        else:
            payload = None
            for preferred_type in ("workflow", "site", "provider", "skill"):
                try:
                    payload = show_object(
                        args.object_id,
                        vault_root=getattr(args, "vault_root", None),
                        object_type=preferred_type,
                    )
                    break
                except SiteOpsRegistryError:
                    continue
            if payload is None:
                raise SiteOpsRegistryError(f"SiteOps object not found: {args.object_id}")
    except SiteOpsRegistryError as exc:
        print(json.dumps({"ok": False, "reason": str(exc)}, indent=2) if getattr(args, "output_json", False) else f"ERROR: {exc}")
        return 1

    result = {"ok": True, "object": payload}
    lines = [
        "ChaseOS SiteOps Object",
        f"  id: {args.object_id}",
        f"  type: {payload.get('_registry_kind')}",
        f"  display_name: {payload.get('display_name')}",
        f"  status: {payload.get('status')}",
        f"  path: {payload.get('_registry_path')}",
    ]
    return _print_json_or_text(args, result, lines)


def cmd_siteops_validate(args: argparse.Namespace) -> int:
    try:
        payload = validate_registry(
            vault_root=getattr(args, "vault_root", None),
            object_id=getattr(args, "object_id", None),
        )
    except SiteOpsRegistryError as exc:
        print(f"ERROR: {exc}")
        return 1

    lines = [
        "ChaseOS SiteOps Validation",
        f"  ok: {payload['ok']}",
        f"  registry_root: {payload['registry_root']}",
        f"  counts: {payload['counts']}",
        f"  errors: {len(payload['errors'])}",
        f"  warnings: {len(payload['warnings'])}",
    ]
    for error in payload["errors"]:
        lines.append(f"  ERROR: {error}")
    for warning in payload["warnings"]:
        lines.append(f"  WARN: {warning}")
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_dry_run(args: argparse.Namespace) -> int:
    try:
        if not getattr(args, "tenant_id", None) or not getattr(args, "user_id", None):
            raise SiteOpsError("siteops dry-run requires --tenant and --user for production-scoped runs")
        inputs = parse_cli_inputs(getattr(args, "inputs", None))
        payload = run_siteops_dry_run(
            root=getattr(args, "vault_root", None),
            workflow_id=args.workflow_id,
            tenant_id=getattr(args, "tenant_id", None),
            workspace_id=getattr(args, "workspace_id", None) or DEFAULT_LOCAL_SCOPE["workspace_id"],
            user_id=getattr(args, "user_id", None),
            inputs=inputs,
            action=getattr(args, "action", "dry_run"),
            write_artifacts=getattr(args, "write_audit", False),
        )
        status = payload["run"]["status"]
        payload["status"] = status
        payload.setdefault("dry_run", {"workflow_id": payload["run"]["workflow_id"], "would_execute": payload.get("would_execute", False)})
    except (SiteOpsRegistryError, SiteOpsError) as exc:
        if getattr(args, "output_json", False):
            print(json.dumps({"ok": False, "reason": str(exc)}, indent=2))
        else:
            print(f"ERROR: {exc}")
        return 1

    result = payload
    run = payload["run"]
    provider = payload.get("provider", {})
    lines = [
        "ChaseOS SiteOps Dry Run",
        f"  workflow_id: {run['workflow_id']}",
        f"  run_id: {run['run_id']}",
        f"  tenant_id: {run['tenant_id']}",
        f"  workspace_id: {run['workspace_id']}",
        f"  user_id: {run['user_id']}",
        f"  status: {payload['status']}",
        f"  would_execute: {payload['would_execute']}",
        f"  live_execution_status: {payload['live_execution_status']}",
        f"  provider: {provider.get('provider_adapter_id')}",
        f"  credentials_configured: {provider.get('credentials_configured')}",
    ]
    if run.get("audit_ref"):
        lines.append(f"  audit_path: {run['audit_ref']}")
    return _print_json_or_text(args, result, lines)


def cmd_siteops_execute(args: argparse.Namespace) -> int:
    """Execute an approved SiteOps workflow via the live browser executor."""
    from runtime.siteops.executor import SiteOpsApprovalError, SiteOpsExecutorNotBuiltError
    try:
        inputs = parse_cli_inputs(getattr(args, "inputs", None))
        payload = run_siteops_live(
            args.workflow_id,
            approval_id=args.approval_id,
            inputs=inputs,
            tenant_id=getattr(args, "tenant_id", None),
            workspace_id=getattr(args, "workspace_id", None) or DEFAULT_LOCAL_SCOPE["workspace_id"],
            user_id=getattr(args, "user_id", None),
            vault_root=getattr(args, "vault_root", None),
        )
    except (SiteOpsApprovalError, SiteOpsExecutorNotBuiltError, SiteOpsError) as exc:
        if getattr(args, "output_json", False):
            print(json.dumps({"ok": False, "reason": str(exc)}, indent=2))
        else:
            print(f"ERROR: {exc}")
        return 1

    lines = [
        "ChaseOS SiteOps Execute",
        f"  workflow_id:           {payload.get('workflow_id')}",
        f"  run_id:                {payload.get('run_id')}",
        f"  approval_id:           {payload.get('approval_id')}",
        f"  executor_kind:         {payload.get('executor_kind')}",
        f"  adapter_mode:          {payload.get('adapter_mode')}",
        f"  live_execution_status: {payload.get('live_execution_status')}",
        f"  ok:                    {payload.get('ok')}",
        f"  is_stub:               {payload.get('is_stub')}",
        f"  char_count:            {payload.get('char_count', 0)}",
        f"  quarantine_path:       {payload.get('quarantine_path')}",
        f"  capture_id:            {payload.get('capture_id')}",
        f"  audit_ref:             {payload.get('audit_ref')}",
    ]
    if payload.get("error"):
        lines.append(f"  error: {payload['error']}")
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_list(args: argparse.Namespace) -> int:
    """List untrusted browser skill candidates without exposing raw content."""
    try:
        root = _vault_root_arg(args)
        candidates = list_candidate_records(root)
        storage = storage_reconciliation(root)
    except (BrowserSkillCandidateError, RuntimeError, ValueError) as exc:
        return _error(args, exc)

    payload = {
        "ok": True,
        "count": len(candidates),
        "candidates": candidates,
        "storage": storage,
        "activation_allowed": False,
        "raw_content_visible": False,
    }
    lines = [
        "ChaseOS SiteOps Browser Skill Candidates",
        f"  candidate_home: {storage['candidate_home']}",
        f"  count: {len(candidates)}",
        "  activation_allowed: false",
    ]
    for item in candidates:
        validation = item.get("validation") or {}
        lines.append(
            "  - "
            f"{item.get('candidate_id')}: "
            f"{item.get('proposed_skill_id') or 'no-skill-id'} "
            f"({item.get('status')}, validator_ok={validation.get('ok')})"
        )
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_show(args: argparse.Namespace) -> int:
    """Show a redacted untrusted browser skill candidate summary."""
    try:
        root = _vault_root_arg(args)
        candidate = show_candidate_record(args.candidate_id, root)
        storage = storage_reconciliation(root)
    except (BrowserSkillCandidateError, RuntimeError, ValueError) as exc:
        return _error(args, exc)

    payload = {
        "ok": True,
        "candidate": candidate,
        "storage": storage,
        "activation_allowed": False,
        "raw_content_visible": False,
    }
    validation = candidate.get("validation") or {}
    lines = [
        "ChaseOS SiteOps Browser Skill Candidate",
        f"  candidate_id: {candidate.get('candidate_id')}",
        f"  proposed_skill_id: {candidate.get('proposed_skill_id')}",
        f"  status: {candidate.get('status')}",
        f"  path: {candidate.get('path')}",
        f"  validator_ok: {validation.get('ok')}",
        "  raw_content_visible: false",
        "  activation_allowed: false",
    ]
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_preflight(args: argparse.Namespace) -> int:
    """Compute a non-mutating browser skill candidate promotion preflight."""
    try:
        payload = preflight_candidate_promotion(args.candidate_id, _vault_root_arg(args))
    except (BrowserSkillCandidateError, RuntimeError, ValueError) as exc:
        return _error(args, exc)

    target = payload.get("target") or {}
    lines = [
        "ChaseOS SiteOps Browser Skill Candidate Preflight",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        f"  preflight_status: {payload.get('preflight_status')}",
        f"  target_path: {target.get('path')}",
        f"  target_exists: {target.get('exists')}",
        "  writes_performed: false",
        "  activation_allowed: false",
        "  promotion_allowed: false",
    ]
    for blocker in payload.get("blockers") or []:
        lines.append(f"  BLOCKER: {blocker}")
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_request_promotion(args: argparse.Namespace) -> int:
    """Compute a non-mutating browser skill candidate promotion approval contract."""
    try:
        tenant_id = getattr(args, "tenant_id", None)
        user_id = getattr(args, "user_id", None)
        workspace_id = getattr(args, "workspace_id", None) or DEFAULT_LOCAL_SCOPE["workspace_id"]
        write_approval = bool(getattr(args, "write_approval_request", False) or getattr(args, "write_approval", False))
        scope_requested = bool(tenant_id or user_id or getattr(args, "workspace_id", None))
        if scope_requested or write_approval:
            if not tenant_id or not user_id:
                raise SiteOpsError("scoped candidate promotion requests require --tenant and --user")
            payload = request_scoped_candidate_promotion(
                args.candidate_id,
                _vault_root_arg(args),
                tenant_id=tenant_id,
                workspace_id=workspace_id,
                user_id=user_id,
                requested_by=getattr(args, "requested_by", None),
                write_approval=write_approval,
            )
        else:
            payload = candidate_promotion_request_contract(
                args.candidate_id,
                _vault_root_arg(args),
                requested_by=getattr(args, "requested_by", None),
                tenant_id=tenant_id,
                workspace_id=workspace_id if tenant_id or user_id or getattr(args, "workspace_id", None) else None,
                user_id=user_id,
            )
    except (BrowserSkillCandidateError, RuntimeError, ValueError, SiteOpsError) as exc:
        return _error(args, exc)

    request = payload.get("approval_request") or {}
    target = request.get("target") or {}
    scope = payload.get("scope") or {}
    lines = [
        "ChaseOS SiteOps Browser Skill Candidate Promotion Request Contract",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        f"  contract_status: {payload.get('contract_status')}",
        f"  requested_by: {request.get('requested_by')}",
        f"  tenant_id: {scope.get('tenant_id')}",
        f"  workspace_id: {scope.get('workspace_id')}",
        f"  user_id: {scope.get('user_id')}",
        f"  trusted_skill_path: {target.get('trusted_skill_path')}",
        f"  approval_request_written: {str(payload.get('approval_request_written', False)).lower()}",
        f"  run_record_written: {str(payload.get('siteops_run_written', False)).lower()}",
        f"  audit_event_written: {str(payload.get('audit_written', False)).lower()}",
        "  trusted_skill_write_allowed: false",
        "  siteops_skill_card_write_allowed: false",
        "  browser_execution_allowed: false",
    ]
    if payload.get("approval"):
        lines.append(f"  approval_id: {payload['approval'].get('approval_id')}")
    if payload.get("run_ref"):
        lines.append(f"  run_ref: {payload.get('run_ref')}")
    for blocker in payload.get("blockers") or []:
        lines.append(f"  BLOCKER: {blocker}")
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_approvals(args: argparse.Namespace) -> int:
    """List Browser Skill candidate approval requests with provenance."""
    try:
        payload = list_candidate_promotion_approvals(
            _vault_root_arg(args),
            tenant_id=getattr(args, "tenant_id", None) or DEFAULT_LOCAL_SCOPE["tenant_id"],
            workspace_id=getattr(args, "workspace_id", None),
            status=getattr(args, "status", None),
            include_executor_preflight=bool(getattr(args, "include_executor_preflight", False)),
            include_activation_boundary=bool(getattr(args, "include_activation_boundary", False)),
            include_bound_approval_request_spec=bool(getattr(args, "include_bound_approval_request_spec", False)),
            include_readiness_summary=bool(getattr(args, "include_readiness_summary", False)),
        )

    except (BrowserSkillCandidateError, RuntimeError, ValueError, SiteOpsError) as exc:
        return _error(args, exc)

    lines = [
        "ChaseOS SiteOps Browser Skill Candidate Approvals",
        f"  tenant_id: {payload.get('scope', {}).get('tenant_id')}",
        f"  workspace_id: {payload.get('scope', {}).get('workspace_id')}",
        f"  status_filter: {payload.get('status_filter')}",
        f"  count: {payload.get('count')}",
        "  writes_performed: false",
    ]
    for item in payload.get("approvals") or []:
        provenance = item.get("approval_provenance") or {}
        suffix = ""
        if item.get("executor_preflight_status"):
            suffix += f" executor_preflight={item.get('executor_preflight_status')}"
        if item.get("activation_boundary_status"):
            suffix += f" activation_boundary={item.get('activation_boundary_status')}"
        if item.get("bound_approval_request_spec_status"):
            suffix += f" bound_approval_spec={item.get('bound_approval_request_spec_status')}"
        lines.append(
            "  - "
            f"{item.get('approval_id')}: "
            f"candidate={item.get('candidate_id') or 'unknown'} "
            f"skill={item.get('proposed_skill_id') or 'unknown'} "
            f"status={item.get('approval_status')} "
            f"provenance={provenance.get('provenance_status')}"
            f"{suffix}"
        )
    summary = payload.get("readiness_summary") or {}
    if summary:
        lines.append("  readiness_summary:")
        lines.append(f"    approvals: {summary.get('approval_count')}")
        lines.append(f"    approval_status_counts: {summary.get('approval_status_counts')}")
        lines.append(f"    apply_contract_status_counts: {summary.get('apply_contract_status_counts')}")
        if summary.get("executor_preflight_status_counts"):
            lines.append(f"    executor_preflight_status_counts: {summary.get('executor_preflight_status_counts')}")
        if summary.get("activation_boundary_status_counts"):
            lines.append(f"    activation_boundary_status_counts: {summary.get('activation_boundary_status_counts')}")
        if summary.get("bound_approval_request_spec_status_counts"):
            lines.append(
                "    bound_approval_request_spec_status_counts: "
                f"{summary.get('bound_approval_request_spec_status_counts')}"
            )
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_apply_contract(args: argparse.Namespace) -> int:
    """Compute a non-mutating scoped browser skill candidate apply contract."""
    try:
        payload = candidate_promotion_apply_contract(
            args.candidate_id,
            _vault_root_arg(args),
            tenant_id=getattr(args, "tenant_id", None),
            workspace_id=getattr(args, "workspace_id", None) or DEFAULT_LOCAL_SCOPE["workspace_id"],
            user_id=getattr(args, "user_id", None),
            approval_id=args.approval_id,
        )
    except (BrowserSkillCandidateError, RuntimeError, ValueError, SiteOpsError) as exc:
        return _error(args, exc)

    apply_contract = payload.get("apply_contract") or {}
    provenance = payload.get("approval_provenance") or {}
    lines = [
        "ChaseOS SiteOps Browser Skill Candidate Apply Contract",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        f"  approval_id: {apply_contract.get('approval_id')}",
        f"  apply_contract_status: {apply_contract.get('apply_contract_status')}",
        f"  approval_provenance_status: {provenance.get('provenance_status')}",
        "  writes_performed: false",
        "  trusted_skill_write_allowed: false",
        "  siteops_skill_card_write_allowed: false",
        "  browser_execution_allowed: false",
    ]
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_approval_rebind_spec(args: argparse.Namespace) -> int:
    """Compute a no-write approval rebind/supersession spec."""
    try:
        payload = candidate_promotion_approval_rebind_spec(
            args.candidate_id,
            _vault_root_arg(args),
            tenant_id=getattr(args, "tenant_id", None),
            workspace_id=getattr(args, "workspace_id", None) or DEFAULT_LOCAL_SCOPE["workspace_id"],
            user_id=getattr(args, "user_id", None),
            approval_id=args.approval_id,
        )
    except (BrowserSkillCandidateError, RuntimeError, ValueError, SiteOpsError) as exc:
        return _error(args, exc)

    provenance = payload.get("approval_provenance") or {}
    lines = [
        "ChaseOS SiteOps Browser Skill Candidate Approval Rebind Spec",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        f"  approval_id: {args.approval_id}",
        f"  approval_status: {payload.get('approval_status')}",
        f"  approval_provenance_status: {provenance.get('provenance_status')}",
        f"  approval_rebind_spec_status: {payload.get('approval_rebind_spec_status')}",
        f"  review_decision: {payload.get('review_decision')}",
        "  legacy_approval_mutation_allowed: false",
        "  replacement_approval_request_written: false",
        "  writes_performed: false",
        "  trusted_skill_write_allowed: false",
        "  siteops_skill_card_write_allowed: false",
        "  browser_execution_allowed: false",
    ]
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_bound_approval_request_spec(args: argparse.Namespace) -> int:
    """Compute a no-write bound replacement approval artifact contract."""
    try:
        payload = candidate_promotion_bound_approval_request_spec(
            args.candidate_id,
            _vault_root_arg(args),
            tenant_id=getattr(args, "tenant_id", None),
            workspace_id=getattr(args, "workspace_id", None) or DEFAULT_LOCAL_SCOPE["workspace_id"],
            user_id=getattr(args, "user_id", None),
            approval_id=args.approval_id,
        )
    except (BrowserSkillCandidateError, RuntimeError, ValueError, SiteOpsError) as exc:
        return _error(args, exc)

    lines = [
        "ChaseOS SiteOps Browser Skill Candidate Bound Approval Request Spec",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        f"  approval_id: {args.approval_id}",
        f"  bound_approval_request_spec_status: {payload.get('bound_approval_request_spec_status')}",
        f"  review_decision: {payload.get('review_decision')}",
        "  approval_request_artifact_written: false",
        "  legacy_approval_mutation_allowed: false",
        "  approval_decision_written: false",
        "  writes_performed: false",
        "  trusted_skill_write_allowed: false",
        "  siteops_skill_card_write_allowed: false",
        "  browser_execution_allowed: false",
    ]
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_bound_approval_writer_design(args: argparse.Namespace) -> int:
    """Compute a no-write bound approval writer design packet."""
    try:
        payload = candidate_promotion_bound_approval_writer_design(
            args.candidate_id,
            _vault_root_arg(args),
            tenant_id=getattr(args, "tenant_id", None),
            workspace_id=getattr(args, "workspace_id", None) or DEFAULT_LOCAL_SCOPE["workspace_id"],
            user_id=getattr(args, "user_id", None),
            approval_id=args.approval_id,
        )
    except (BrowserSkillCandidateError, RuntimeError, ValueError, SiteOpsError) as exc:
        return _error(args, exc)

    target = payload.get("target_path_preview") or {}
    lines = [
        "ChaseOS SiteOps Browser Skill Candidate Bound Approval Writer Design",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        f"  approval_id: {args.approval_id}",
        f"  bound_approval_writer_design_status: {payload.get('bound_approval_writer_design_status')}",
        f"  review_decision: {payload.get('review_decision')}",
        f"  target_exists: {str(target.get('target_exists', False)).lower()}",
        "  approval_request_artifact_written: false",
        "  bound_approval_writer_implemented: false",
        "  bound_approval_audit_event_written: false",
        "  legacy_approval_mutation_allowed: false",
        "  approval_decision_written: false",
        "  writes_performed: false",
        "  trusted_skill_write_allowed: false",
        "  siteops_skill_card_write_allowed: false",
        "  browser_execution_allowed: false",
    ]
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_bound_approval_writer_preflight(args: argparse.Namespace) -> int:
    """Compute a no-write invocation preflight for a future bound approval writer."""
    try:
        payload = candidate_promotion_bound_approval_writer_preflight(
            args.candidate_id,
            _vault_root_arg(args),
            tenant_id=getattr(args, "tenant_id", None),
            workspace_id=getattr(args, "workspace_id", None) or DEFAULT_LOCAL_SCOPE["workspace_id"],
            user_id=getattr(args, "user_id", None),
            approval_id=args.approval_id,
        )
    except (BrowserSkillCandidateError, RuntimeError, ValueError, SiteOpsError) as exc:
        return _error(args, exc)

    target = payload.get("target_path_preview") or {}
    marker = payload.get("idempotency_marker_preview") or {}
    gate = payload.get("trusted_apply_gate_posture") or {}
    lines = [
        "ChaseOS SiteOps Browser Skill Candidate Bound Approval Writer Preflight",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        f"  approval_id: {args.approval_id}",
        f"  bound_approval_writer_preflight_status: {payload.get('bound_approval_writer_preflight_status')}",
        f"  review_decision: {payload.get('review_decision')}",
        f"  target_exists: {str(target.get('target_exists', False)).lower()}",
        f"  idempotency_marker_exists: {str(marker.get('marker_exists', False)).lower()}",
        f"  trusted_apply_gate_allowed: {str(gate.get('allowed', False)).lower()}",
        "  approval_request_artifact_written: false",
        "  bound_approval_writer_implemented: false",
        "  bound_approval_preflight_marker_written: false",
        "  bound_approval_recovery_marker_written: false",
        "  legacy_approval_mutation_allowed: false",
        "  approval_decision_written: false",
        "  writes_performed: false",
        "  trusted_skill_write_allowed: false",
        "  siteops_skill_card_write_allowed: false",
        "  browser_execution_allowed: false",
    ]
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_bound_approval_writer_implementation_request(args: argparse.Namespace) -> int:
    """Compute a no-write operator request packet for a future bound approval writer."""
    try:
        payload = candidate_promotion_bound_approval_writer_implementation_request(
            args.candidate_id,
            _vault_root_arg(args),
            tenant_id=getattr(args, "tenant_id", None),
            workspace_id=getattr(args, "workspace_id", None) or DEFAULT_LOCAL_SCOPE["workspace_id"],
            user_id=getattr(args, "user_id", None),
            approval_id=args.approval_id,
        )
    except (BrowserSkillCandidateError, RuntimeError, ValueError, SiteOpsError) as exc:
        return _error(args, exc)

    lines = [
        "ChaseOS SiteOps Browser Skill Candidate Bound Approval Writer Implementation Request",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        f"  approval_id: {args.approval_id}",
        "  bound_approval_writer_implementation_request_status: "
        f"{payload.get('bound_approval_writer_implementation_request_status')}",
        f"  review_decision: {payload.get('review_decision')}",
        "  implementation_request_artifact_written: false",
        "  approval_request_artifact_written: false",
        "  bound_approval_writer_implemented: false",
        "  bound_approval_writer_execution_allowed: false",
        "  approval_decision_written: false",
        "  writes_performed: false",
        "  trusted_skill_write_allowed: false",
        "  siteops_skill_card_write_allowed: false",
        "  browser_execution_allowed: false",
    ]
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_bound_approval_writer_implementation_approval(args: argparse.Namespace) -> int:
    """Compute a no-write approval/rejection packet for a future bound approval writer implementation."""
    try:
        payload = candidate_promotion_bound_approval_writer_implementation_approval(
            args.candidate_id,
            _vault_root_arg(args),
            tenant_id=getattr(args, "tenant_id", None),
            workspace_id=getattr(args, "workspace_id", None) or DEFAULT_LOCAL_SCOPE["workspace_id"],
            user_id=getattr(args, "user_id", None),
            approval_id=args.approval_id,
            decision=args.decision,
            actor=args.actor,
            reason=getattr(args, "reason", None),
        )
    except (BrowserSkillCandidateError, RuntimeError, ValueError, SiteOpsError) as exc:
        return _error(args, exc)

    lines = [
        "ChaseOS SiteOps Browser Skill Candidate Bound Approval Writer Implementation Approval",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        f"  approval_id: {args.approval_id}",
        f"  decision: {payload.get('decision')}",
        f"  actor: {payload.get('actor')}",
        "  bound_approval_writer_implementation_approval_status: "
        f"{payload.get('bound_approval_writer_implementation_approval_status')}",
        f"  review_decision: {payload.get('review_decision')}",
        f"  implementation_patch_allowed_next_pass: {str(payload.get('implementation_patch_allowed_next_pass', False)).lower()}",
        "  implementation_approval_record_written: false",
        "  replacement_approval_request_written: false",
        "  bound_approval_writer_implemented: false",
        "  bound_approval_writer_execution_allowed: false",
        "  approval_decision_written: false",
        "  writes_performed: false",
        "  trusted_skill_write_allowed: false",
        "  siteops_skill_card_write_allowed: false",
        "  browser_execution_allowed: false",
    ]
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_bound_approval_writer_implementation(args: argparse.Namespace) -> int:
    """Run the bounded replacement approval writer, optionally writing the replacement request."""
    try:
        payload = candidate_promotion_bound_approval_writer_implementation(
            args.candidate_id,
            _vault_root_arg(args),
            tenant_id=getattr(args, "tenant_id", None),
            workspace_id=getattr(args, "workspace_id", None) or DEFAULT_LOCAL_SCOPE["workspace_id"],
            user_id=getattr(args, "user_id", None),
            approval_id=args.approval_id,
            actor=args.actor,
            reason=getattr(args, "reason", None),
            write_replacement_approval=bool(getattr(args, "write_replacement_approval", False)),
        )
    except (BrowserSkillCandidateError, RuntimeError, ValueError, SiteOpsError, FileExistsError) as exc:
        return _error(args, exc)

    lines = [
        "ChaseOS SiteOps Browser Skill Candidate Bound Approval Writer Implementation",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        f"  approval_id: {args.approval_id}",
        f"  actor: {payload.get('actor')}",
        "  bound_approval_writer_implementation_status: "
        f"{payload.get('bound_approval_writer_implementation_status')}",
        f"  review_decision: {payload.get('review_decision')}",
        f"  write_replacement_approval_requested: {str(payload.get('write_replacement_approval_requested', False)).lower()}",
        f"  replacement_approval_request_written: {str(payload.get('replacement_approval_request_written', False)).lower()}",
        f"  bound_approval_run_record_written: {str(payload.get('bound_approval_run_record_written', False)).lower()}",
        f"  bound_approval_audit_event_written: {str(payload.get('bound_approval_audit_event_written', False)).lower()}",
        f"  bound_approval_idempotency_marker_written: {str(payload.get('bound_approval_idempotency_marker_written', False)).lower()}",
        f"  bound_approval_recovery_marker_written: {str(payload.get('bound_approval_recovery_marker_written', False)).lower()}",
        f"  writes_performed: {str(payload.get('writes_performed', False)).lower()}",
        "  approval_decision_written: false",
        "  legacy_approval_mutation_allowed: false",
        "  trusted_skill_write_allowed: false",
        "  siteops_skill_card_write_allowed: false",
        "  browser_execution_allowed: false",
    ]
    if payload.get("approval_ref"):
        lines.append(f"  approval_ref: {payload.get('approval_ref')}")
    if payload.get("audit_ref"):
        lines.append(f"  audit_ref: {payload.get('audit_ref')}")
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_replacement_approval_decision_consumption(args: argparse.Namespace) -> int:
    """Decide a bound replacement approval without consuming it or writing trusted artifacts."""
    try:
        payload = candidate_promotion_replacement_approval_decision_consumption(
            args.candidate_id,
            _vault_root_arg(args),
            tenant_id=getattr(args, "tenant_id", None),
            workspace_id=getattr(args, "workspace_id", None) or DEFAULT_LOCAL_SCOPE["workspace_id"],
            user_id=getattr(args, "user_id", None),
            replacement_approval_id=args.replacement_approval_id,
            actor=args.actor,
            decision=args.decision,
            reason=getattr(args, "reason", None),
            write_approval_decision=bool(getattr(args, "write_approval_decision", False)),
        )
    except (BrowserSkillCandidateError, RuntimeError, ValueError, SiteOpsError) as exc:
        return _error(args, exc)

    lines = [
        "ChaseOS SiteOps Browser Skill Candidate Replacement Approval Decision/Consumption",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        f"  replacement_approval_id: {payload.get('replacement_approval_id')}",
        f"  actor: {payload.get('actor')}",
        f"  decision: {payload.get('decision')}",
        f"  replacement_approval_decision_status: {payload.get('replacement_approval_decision_status')}",
        f"  replacement_approval_consumption_status: {payload.get('replacement_approval_consumption_status')}",
        f"  replacement_approval_consumption_ready: {str(payload.get('replacement_approval_consumption_ready', False)).lower()}",
        f"  approval_decision_write_requested: {str(payload.get('approval_decision_write_requested', False)).lower()}",
        f"  approval_decision_written: {str(payload.get('approval_decision_written', False)).lower()}",
        "  approval_consumed: false",
        "  legacy_approval_mutation_allowed: false",
        "  trusted_skill_write_allowed: false",
        "  siteops_skill_card_write_allowed: false",
        "  browser_execution_allowed: false",
        "  agent_bus_enqueue_allowed: false",
        "  provider_api_call_allowed: false",
        "  activation_allowed: false",
        "  canonical_writeback_allowed: false",
    ]
    if payload.get("replacement_approval_ref"):
        lines.append(f"  replacement_approval_ref: {payload.get('replacement_approval_ref')}")
    if payload.get("audit_ref"):
        lines.append(f"  audit_ref: {payload.get('audit_ref')}")
    return _print_json_or_text(args, payload, lines)



def cmd_siteops_candidates_gate_apply_design(args: argparse.Namespace) -> int:
    """Compute a denied-by-default Gate apply design packet."""
    try:
        payload = candidate_promotion_gate_apply_design(
            args.candidate_id,
            _vault_root_arg(args),
            tenant_id=getattr(args, "tenant_id", None),
            workspace_id=getattr(args, "workspace_id", None) or DEFAULT_LOCAL_SCOPE["workspace_id"],
            user_id=getattr(args, "user_id", None),
            approval_id=args.approval_id,
        )
    except (BrowserSkillCandidateError, RuntimeError, ValueError, SiteOpsError) as exc:
        return _error(args, exc)

    provenance = payload.get("approval_provenance") or {}
    lines = [
        "ChaseOS SiteOps Browser Skill Candidate Gate Apply Design",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        f"  gate_apply_design_status: {payload.get('gate_apply_design_status')}",
        f"  approval_provenance_status: {provenance.get('provenance_status')}",
        f"  gate_operation: {payload.get('gate_operation')}",
        f"  gate_operation_allowed: {str(payload.get('gate_operation_allowed', False)).lower()}",
        "  writes_performed: false",
        "  apply_execution_allowed: false",
        "  trusted_skill_write_allowed: false",
        "  siteops_skill_card_write_allowed: false",
        "  browser_execution_allowed: false",
    ]
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_gate_executor_spec(args: argparse.Namespace) -> int:
    """Compute a fail-closed future Gate executor specification."""
    try:
        payload = candidate_promotion_gate_executor_spec(
            args.candidate_id,
            _vault_root_arg(args),
            tenant_id=getattr(args, "tenant_id", None),
            workspace_id=getattr(args, "workspace_id", None) or DEFAULT_LOCAL_SCOPE["workspace_id"],
            user_id=getattr(args, "user_id", None),
            approval_id=args.approval_id,
        )
    except (BrowserSkillCandidateError, RuntimeError, ValueError, SiteOpsError) as exc:
        return _error(args, exc)

    provenance = payload.get("approval_provenance") or {}
    future_executor = payload.get("future_executor") or {}
    secret_recheck = payload.get("secret_session_exclusion_recheck") or {}
    lines = [
        "ChaseOS SiteOps Browser Skill Candidate Gate Executor Spec",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        f"  executor_spec_status: {payload.get('executor_spec_status')}",
        f"  executor_preflight_status: {payload.get('executor_preflight_status')}",
        f"  gate_apply_design_status: {payload.get('gate_apply_design_status')}",
        f"  approval_provenance_status: {provenance.get('provenance_status')}",
        f"  secret_session_exclusion_rechecked: {str(secret_recheck.get('passed', False)).lower()}",
        f"  gate_operation: {payload.get('gate_operation')}",
        f"  gate_operation_allowed: {str(payload.get('gate_operation_allowed', False)).lower()}",
        f"  future_executor_status: {future_executor.get('implementation_status')}",
        "  writes_performed: false",
        "  executor_enabled: false",
        "  trusted_skill_write_allowed: false",
        "  siteops_skill_card_write_allowed: false",
        "  browser_execution_allowed: false",
    ]
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_gate_allowlist_review(args: argparse.Namespace) -> int:
    """Compute a fail-closed Gate allowlist review packet."""
    try:
        payload = candidate_promotion_gate_allowlist_review(
            args.candidate_id,
            _vault_root_arg(args),
            tenant_id=getattr(args, "tenant_id", None),
            workspace_id=getattr(args, "workspace_id", None) or DEFAULT_LOCAL_SCOPE["workspace_id"],
            user_id=getattr(args, "user_id", None),
            approval_id=args.approval_id,
        )
    except (BrowserSkillCandidateError, RuntimeError, ValueError, SiteOpsError) as exc:
        return _error(args, exc)

    provenance = payload.get("approval_provenance") or {}
    secret_recheck = payload.get("secret_session_exclusion_recheck") or {}
    lines = [
        "ChaseOS SiteOps Browser Skill Candidate Gate Allowlist Review",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        f"  allowlist_review_status: {payload.get('allowlist_review_status')}",
        f"  executor_spec_status: {payload.get('executor_spec_status')}",
        f"  approval_provenance_status: {provenance.get('provenance_status')}",
        f"  secret_session_exclusion_rechecked: {str(secret_recheck.get('passed', False)).lower()}",
        f"  gate_operation: {payload.get('gate_operation')}",
        f"  operation_currently_allowlisted: {str(payload.get('operation_currently_allowlisted', False)).lower()}",
        "  allowlist_change_performed: false",
        "  policy_file_write_allowed: false",
        "  writes_performed: false",
        "  executor_enabled: false",
        "  trusted_skill_write_allowed: false",
        "  siteops_skill_card_write_allowed: false",
    ]
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_trusted_executor_design(args: argparse.Namespace) -> int:
    """Compute a fail-closed trusted artifact executor design packet."""
    try:
        payload = candidate_promotion_trusted_executor_design(
            args.candidate_id,
            _vault_root_arg(args),
            tenant_id=getattr(args, "tenant_id", None),
            workspace_id=getattr(args, "workspace_id", None) or DEFAULT_LOCAL_SCOPE["workspace_id"],
            user_id=getattr(args, "user_id", None),
            approval_id=args.approval_id,
        )
    except (BrowserSkillCandidateError, RuntimeError, ValueError, SiteOpsError) as exc:
        return _error(args, exc)

    provenance = payload.get("approval_provenance") or {}
    lines = [
        "ChaseOS SiteOps Browser Skill Candidate Trusted Executor Design",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        f"  trusted_executor_design_status: {payload.get('trusted_executor_design_status')}",
        f"  allowlist_review_status: {payload.get('allowlist_review_status')}",
        f"  approval_provenance_status: {provenance.get('provenance_status')}",
        f"  gate_operation: {payload.get('gate_operation')}",
        f"  operation_currently_allowlisted: {str(payload.get('operation_currently_allowlisted', False)).lower()}",
        "  executor_implemented: false",
        "  executor_enabled: false",
        "  writes_performed: false",
        "  trusted_skill_write_allowed: false",
        "  siteops_skill_card_write_allowed: false",
    ]
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_executor_review_checklist(args: argparse.Namespace) -> int:
    """Compute a no-write review checklist for a future trusted artifact executor."""
    try:
        payload = candidate_promotion_executor_review_checklist(
            args.candidate_id,
            _vault_root_arg(args),
            tenant_id=getattr(args, "tenant_id", None),
            workspace_id=getattr(args, "workspace_id", None) or DEFAULT_LOCAL_SCOPE["workspace_id"],
            user_id=getattr(args, "user_id", None),
            approval_id=args.approval_id,
        )
    except (BrowserSkillCandidateError, RuntimeError, ValueError, SiteOpsError) as exc:
        return _error(args, exc)

    provenance = payload.get("approval_provenance") or {}
    lines = [
        "ChaseOS SiteOps Browser Skill Candidate Executor Review Checklist",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        f"  executor_review_status: {payload.get('executor_review_status')}",
        f"  trusted_executor_design_status: {payload.get('trusted_executor_design_status')}",
        f"  allowlist_review_status: {payload.get('allowlist_review_status')}",
        f"  approval_provenance_status: {provenance.get('provenance_status')}",
        f"  gate_operation: {payload.get('gate_operation')}",
        f"  operation_currently_allowlisted: {str(payload.get('operation_currently_allowlisted', False)).lower()}",
        "  review_decision: do_not_implement_in_this_pass",
        "  executor_implemented: false",
        "  executor_enabled: false",
        "  writes_performed: false",
        "  trusted_skill_write_allowed: false",
        "  siteops_skill_card_write_allowed: false",
    ]
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_preimplementation_verifier(args: argparse.Namespace) -> int:
    """Run the read-only pre-implementation verifier before any executor patch is proposed."""
    try:
        payload = candidate_promotion_preimplementation_verifier(
            args.candidate_id,
            _vault_root_arg(args),
            tenant_id=getattr(args, "tenant_id", None),
            workspace_id=getattr(args, "workspace_id", None) or DEFAULT_LOCAL_SCOPE["workspace_id"],
            user_id=getattr(args, "user_id", None),
            approval_id=args.approval_id,
        )
    except (BrowserSkillCandidateError, RuntimeError, ValueError, SiteOpsError) as exc:
        return _error(args, exc)

    provenance = payload.get("approval_provenance") or {}
    verifier_checks = payload.get("verifier_checks") or []
    lines = [
        "ChaseOS SiteOps Browser Skill Candidate Pre-Implementation Verifier",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        f"  verifier_verdict: {payload.get('verifier_verdict')}",
        f"  verifier_pass: {str(payload.get('verifier_pass', False)).lower()}",
        f"  checklist_status: {payload.get('checklist_status')}",
        f"  checklist_layer_pass: {str(payload.get('checklist_layer_pass', False)).lower()}",
        f"  approval_provenance_status: {provenance.get('provenance_status')}",
        f"  gate_operation: {payload.get('gate_operation')}",
        f"  operation_currently_allowlisted: {str(payload.get('operation_currently_allowlisted', False)).lower()}",
        "  review_decision: do_not_implement_in_this_pass",
        "  executor_implemented: false",
        "  executor_enabled: false",
        "  writes_performed: false",
        "  trusted_skill_write_allowed: false",
        "  siteops_skill_card_write_allowed: false",
        "  Live guard checks:",
    ]
    for check in verifier_checks:
        status = "PASS" if check.get("passed") else "FAIL"
        lines.append(f"    [{status}] {check.get('check_id')}: {check.get('detail')}")
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_executor_implementation_design_review(args: argparse.Namespace) -> int:
    """Compute a review-only future executor implementation design packet."""
    try:
        payload = candidate_promotion_executor_implementation_design_review(
            args.candidate_id,
            _vault_root_arg(args),
            tenant_id=getattr(args, "tenant_id", None),
            workspace_id=getattr(args, "workspace_id", None) or DEFAULT_LOCAL_SCOPE["workspace_id"],
            user_id=getattr(args, "user_id", None),
            approval_id=args.approval_id,
        )
    except (BrowserSkillCandidateError, RuntimeError, ValueError, SiteOpsError) as exc:
        return _error(args, exc)

    lines = [
        "ChaseOS SiteOps Browser Skill Candidate Executor Implementation Design Review",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        f"  implementation_design_status: {payload.get('implementation_design_status')}",
        f"  verifier_verdict: {payload.get('verifier_verdict')}",
        f"  verifier_pass: {str(payload.get('verifier_pass', False)).lower()}",
        f"  gate_operation: {payload.get('gate_operation')}",
        "  review_decision: patch_plan_only_do_not_implement_in_this_pass",
        "  executor_implemented: false",
        "  executor_enabled: false",
        "  writes_performed: false",
        "  trusted_skill_write_allowed: false",
        "  siteops_skill_card_write_allowed: false",
    ]
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_executor_prewrite_audit_spec(args: argparse.Namespace) -> int:
    """Compute a no-write audit and inactive-artifact spec for a future executor."""
    try:
        payload = candidate_promotion_executor_prewrite_audit_spec(
            args.candidate_id,
            _vault_root_arg(args),
            tenant_id=getattr(args, "tenant_id", None),
            workspace_id=getattr(args, "workspace_id", None) or DEFAULT_LOCAL_SCOPE["workspace_id"],
            user_id=getattr(args, "user_id", None),
            approval_id=args.approval_id,
        )
    except (BrowserSkillCandidateError, RuntimeError, ValueError, SiteOpsError) as exc:
        return _error(args, exc)

    lines = [
        "ChaseOS SiteOps Browser Skill Candidate Executor Prewrite Audit Spec",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        f"  prewrite_audit_spec_status: {payload.get('prewrite_audit_spec_status')}",
        f"  implementation_design_status: {payload.get('implementation_design_status')}",
        f"  gate_operation: {payload.get('gate_operation')}",
        "  review_decision: audit_contract_only_do_not_write_in_this_pass",
        "  audit_events_written: false",
        "  inactive_artifacts_written: false",
        "  executor_implemented: false",
        "  writes_performed: false",
        "  trusted_skill_write_allowed: false",
        "  siteops_skill_card_write_allowed: false",
    ]
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_inactive_artifact_validator(args: argparse.Namespace) -> int:
    """Validate future inactive artifact payload shapes without writing them."""
    try:
        payload = candidate_promotion_inactive_artifact_validator(
            args.candidate_id,
            _vault_root_arg(args),
            tenant_id=getattr(args, "tenant_id", None),
            workspace_id=getattr(args, "workspace_id", None) or DEFAULT_LOCAL_SCOPE["workspace_id"],
            user_id=getattr(args, "user_id", None),
            approval_id=args.approval_id,
        )
    except (BrowserSkillCandidateError, RuntimeError, ValueError, SiteOpsError) as exc:
        return _error(args, exc)

    lines = [
        "ChaseOS SiteOps Browser Skill Candidate Inactive Artifact Validator",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        f"  inactive_artifact_validator_status: {payload.get('inactive_artifact_validator_status')}",
        f"  validation_pass: {str(payload.get('validation_pass', False)).lower()}",
        f"  prewrite_audit_spec_status: {payload.get('prewrite_audit_spec_status')}",
        f"  gate_operation: {payload.get('gate_operation')}",
        "  review_decision: validator_contract_only_do_not_write_in_this_pass",
        "  inactive_artifacts_written: false",
        "  executor_implemented: false",
        "  writes_performed: false",
        "  trusted_skill_write_allowed: false",
        "  siteops_skill_card_write_allowed: false",
    ]
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_trusted_inactive_artifact_writer_preflight(args: argparse.Namespace) -> int:
    """Preflight future inactive trusted artifact writes without writing them."""
    try:
        payload = candidate_promotion_trusted_inactive_artifact_writer_preflight(
            args.candidate_id,
            _vault_root_arg(args),
            tenant_id=args.tenant_id,
            workspace_id=args.workspace_id,
            user_id=args.user_id,
            replacement_approval_id=args.replacement_approval_id,
        )
    except (BrowserSkillCandidateError, SiteOpsError, FileNotFoundError) as exc:
        return _error(args, exc)
    lines = [
        "SiteOps trusted inactive artifact writer preflight:",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        f"  trusted_inactive_artifact_writer_preflight_status: {payload.get('trusted_inactive_artifact_writer_preflight_status')}",
        f"  replacement_approval_consumption_status: {payload.get('replacement_approval_consumption_status')}",
        f"  write_preflight_pass: {str(payload.get('write_preflight_pass', False)).lower()}",
        "  writes_performed: false",
        "  inactive_artifacts_written: false",
        "  trusted_skill_write_allowed: false",
        "  siteops_skill_card_write_allowed: false",
        "  activation_allowed: false",
        "  browser_execution_allowed: false",
        "  agent_bus_enqueue_allowed: false",
    ]
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_trusted_inactive_artifact_writer_implementation_request(args: argparse.Namespace) -> int:
    """Return a no-write implementation request packet for the inactive artifact writer."""
    try:
        payload = candidate_promotion_trusted_inactive_artifact_writer_implementation_request(
            args.candidate_id,
            _vault_root_arg(args),
            tenant_id=args.tenant_id,
            workspace_id=args.workspace_id,
            user_id=args.user_id,
            replacement_approval_id=args.replacement_approval_id,
        )
    except (BrowserSkillCandidateError, SiteOpsError, FileNotFoundError) as exc:
        return _error(args, exc)
    lines = [
        "SiteOps trusted inactive artifact writer implementation request:",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        f"  trusted_inactive_artifact_writer_preflight_status: {payload.get('trusted_inactive_artifact_writer_preflight_status')}",
        f"  trusted_inactive_artifact_writer_implementation_request_status: {payload.get('trusted_inactive_artifact_writer_implementation_request_status')}",
        f"  request_ready_no_write: {str(payload.get('request_ready_no_write', False)).lower()}",
        "  implementation_request_artifact_written: false",
        "  writes_performed: false",
        "  inactive_artifacts_written: false",
        "  trusted_skill_write_allowed: false",
        "  siteops_skill_card_write_allowed: false",
        "  activation_allowed: false",
        "  browser_execution_allowed: false",
        "  agent_bus_enqueue_allowed: false",
    ]
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_trusted_inactive_artifact_writer_implementation_approval(args: argparse.Namespace) -> int:
    """Return a no-write approve/reject packet for the inactive artifact writer implementation."""
    try:
        payload = candidate_promotion_trusted_inactive_artifact_writer_implementation_approval(
            args.candidate_id,
            _vault_root_arg(args),
            tenant_id=args.tenant_id,
            workspace_id=args.workspace_id,
            user_id=args.user_id,
            replacement_approval_id=args.replacement_approval_id,
            decision=args.decision,
            actor=args.actor,
            reason=getattr(args, "reason", None),
        )
    except (BrowserSkillCandidateError, SiteOpsError, FileNotFoundError, ValueError) as exc:
        return _error(args, exc)
    lines = [
        "SiteOps trusted inactive artifact writer implementation approval:",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        f"  replacement_approval_id: {payload.get('replacement_approval_id')}",
        f"  decision: {payload.get('decision')}",
        f"  actor: {payload.get('actor')}",
        "  trusted_inactive_artifact_writer_implementation_approval_status: "
        f"{payload.get('trusted_inactive_artifact_writer_implementation_approval_status')}",
        f"  review_decision: {payload.get('review_decision')}",
        f"  implementation_patch_allowed_next_pass: {str(payload.get('implementation_patch_allowed_next_pass', False)).lower()}",
        "  implementation_approval_record_written: false",
        "  implementation_request_artifact_written: false",
        "  approval_decision_written: false",
        "  writes_performed: false",
        "  inactive_artifacts_written: false",
        "  trusted_skill_write_allowed: false",
        "  siteops_skill_card_write_allowed: false",
        "  activation_allowed: false",
        "  browser_execution_allowed: false",
        "  agent_bus_enqueue_allowed: false",
    ]
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_trusted_inactive_artifact_writer_implementation(args: argparse.Namespace) -> int:
    """Run or preview the bounded inactive trusted artifact writer."""
    try:
        payload = candidate_promotion_trusted_inactive_artifact_writer_implementation(
            args.candidate_id,
            _vault_root_arg(args),
            tenant_id=args.tenant_id,
            workspace_id=args.workspace_id,
            user_id=args.user_id,
            replacement_approval_id=args.replacement_approval_id,
            actor=args.actor,
            reason=getattr(args, "reason", None),
            write_inactive_artifacts=getattr(args, "write_inactive_artifacts", False),
        )
    except (BrowserSkillCandidateError, SiteOpsError, FileNotFoundError, ValueError) as exc:
        return _error(args, exc)
    lines = [
        "SiteOps trusted inactive artifact writer implementation:",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        f"  replacement_approval_id: {payload.get('replacement_approval_id')}",
        "  trusted_inactive_artifact_writer_implementation_status: "
        f"{payload.get('trusted_inactive_artifact_writer_implementation_status')}",
        f"  writer_ready_to_write: {str(payload.get('writer_ready_to_write', False)).lower()}",
        f"  gate_operation_allowed: {str(payload.get('gate_operation_allowed', False)).lower()}",
        f"  write_inactive_artifacts_requested: {str(payload.get('write_inactive_artifacts_requested', False)).lower()}",
        f"  inactive_artifacts_written: {str(payload.get('inactive_artifacts_written', False)).lower()}",
        f"  browser_skill_artifact_written: {str(payload.get('browser_skill_artifact_written', False)).lower()}",
        f"  siteops_skill_card_artifact_written: {str(payload.get('siteops_skill_card_artifact_written', False)).lower()}",
        f"  approval_consumed: {str(payload.get('approval_consumed', False)).lower()}",
        f"  activation_allowed: {str(payload.get('activation_allowed', False)).lower()}",
        f"  browser_execution_allowed: {str(payload.get('browser_execution_allowed', False)).lower()}",
        f"  agent_bus_enqueue_allowed: {str(payload.get('agent_bus_enqueue_allowed', False)).lower()}",
        f"  canonical_writeback_allowed: {str(payload.get('canonical_writeback_allowed', False)).lower()}",
    ]
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_apply_trusted_candidate_artifacts(args: argparse.Namespace) -> int:
    """Invoke the canonical guarded executor entrypoint for trusted candidate artifacts."""
    try:
        payload = apply_trusted_candidate_artifacts(
            args.candidate_id,
            _vault_root_arg(args),
            tenant_id=args.tenant_id,
            workspace_id=args.workspace_id,
            user_id=args.user_id,
            replacement_approval_id=args.replacement_approval_id,
            actor=args.actor,
            reason=getattr(args, "reason", None),
            write_inactive_artifacts=getattr(args, "write_inactive_artifacts", False),
        )
    except (BrowserSkillCandidateError, SiteOpsError, FileNotFoundError, ValueError) as exc:
        return _error(args, exc)
    lines = [
        "SiteOps apply trusted candidate artifacts:",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        f"  executor_entrypoint: {payload.get('executor_entrypoint')}",
        f"  executor_entrypoint_status: {payload.get('executor_entrypoint_status')}",
        "  trusted_inactive_artifact_writer_implementation_status: "
        f"{payload.get('trusted_inactive_artifact_writer_implementation_status')}",
        f"  gate_operation_allowed: {str(payload.get('gate_operation_allowed', False)).lower()}",
        f"  write_inactive_artifacts_requested: {str(payload.get('write_inactive_artifacts_requested', False)).lower()}",
        f"  inactive_artifacts_written: {str(payload.get('inactive_artifacts_written', False)).lower()}",
        f"  approval_consumed: {str(payload.get('approval_consumed', False)).lower()}",
        f"  activation_allowed: {str(payload.get('activation_allowed', False)).lower()}",
        f"  browser_execution_allowed: {str(payload.get('browser_execution_allowed', False)).lower()}",
        f"  agent_bus_enqueue_allowed: {str(payload.get('agent_bus_enqueue_allowed', False)).lower()}",
        f"  canonical_writeback_allowed: {str(payload.get('canonical_writeback_allowed', False)).lower()}",
    ]
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_trusted_inactive_artifact_writer_live_gate_readiness(args: argparse.Namespace) -> int:
    """Return a no-write live Gate readiness packet for the inactive artifact writer."""
    try:
        payload = candidate_promotion_trusted_inactive_artifact_writer_live_gate_readiness(
            args.candidate_id,
            _vault_root_arg(args),
            tenant_id=args.tenant_id,
            workspace_id=args.workspace_id,
            user_id=args.user_id,
            replacement_approval_id=args.replacement_approval_id,
            actor=args.actor,
            reason=getattr(args, "reason", None),
        )
    except (BrowserSkillCandidateError, SiteOpsError, FileNotFoundError, ValueError) as exc:
        return _error(args, exc)
    lines = [
        "SiteOps trusted inactive artifact writer live Gate readiness:",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        f"  replacement_approval_id: {payload.get('replacement_approval_id')}",
        "  trusted_inactive_artifact_writer_live_gate_readiness_status: "
        f"{payload.get('trusted_inactive_artifact_writer_live_gate_readiness_status')}",
        f"  gate_patch_ready_for_operator_review: {str(payload.get('gate_patch_ready_for_operator_review', False)).lower()}",
        f"  gate_operation_allowed: {str(payload.get('gate_operation_allowed', False)).lower()}",
        f"  gate_policy_change_performed: {str(payload.get('gate_policy_change_performed', False)).lower()}",
        f"  inactive_artifacts_written: {str(payload.get('inactive_artifacts_written', False)).lower()}",
        f"  approval_consumed: {str(payload.get('approval_consumed', False)).lower()}",
        f"  activation_allowed: {str(payload.get('activation_allowed', False)).lower()}",
        f"  browser_execution_allowed: {str(payload.get('browser_execution_allowed', False)).lower()}",
        f"  agent_bus_enqueue_allowed: {str(payload.get('agent_bus_enqueue_allowed', False)).lower()}",
        f"  canonical_writeback_allowed: {str(payload.get('canonical_writeback_allowed', False)).lower()}",
    ]
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_trusted_inactive_artifact_writer_gate_allowlist_approval_request(
    args: argparse.Namespace,
) -> int:
    """Preview or write a pending Gate allowlist approval request for the inactive writer."""
    try:
        payload = candidate_promotion_trusted_inactive_artifact_writer_gate_allowlist_approval_request(
            args.candidate_id,
            _vault_root_arg(args),
            tenant_id=args.tenant_id,
            workspace_id=args.workspace_id,
            user_id=args.user_id,
            replacement_approval_id=args.replacement_approval_id,
            actor=args.actor,
            requested_by=getattr(args, "requested_by", None),
            reason=getattr(args, "reason", None),
            write_approval_request=getattr(args, "write_approval_request", False),
        )
    except (BrowserSkillCandidateError, SiteOpsError, FileNotFoundError, ValueError) as exc:
        return _error(args, exc)
    lines = [
        "SiteOps trusted inactive artifact writer Gate allowlist approval request:",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        f"  replacement_approval_id: {payload.get('replacement_approval_id')}",
        f"  gate_allowlist_approval_request_status: {payload.get('gate_allowlist_approval_request_status')}",
        f"  gate_patch_ready_for_operator_review: {str(payload.get('gate_patch_ready_for_operator_review', False)).lower()}",
        f"  write_approval_request_requested: {str(payload.get('write_approval_request_requested', False)).lower()}",
        f"  approval_request_written: {str(payload.get('approval_request_written', False)).lower()}",
        f"  approval_id: {payload.get('approval_id')}",
        "  gate_policy_change_performed: false",
        "  allowlist_change_performed: false",
        "  inactive_artifacts_written: false",
        "  approval_consumed: false",
        "  activation_allowed: false",
        "  browser_execution_allowed: false",
        "  agent_bus_enqueue_allowed: false",
        "  canonical_writeback_allowed: false",
    ]
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_trusted_inactive_artifact_writer_gate_allowlist_decision_preflight(
    args: argparse.Namespace,
) -> int:
    """Validate a Gate allowlist approval request before any policy patch."""
    try:
        payload = candidate_promotion_trusted_inactive_artifact_writer_gate_allowlist_decision_preflight(
            args.candidate_id,
            _vault_root_arg(args),
            tenant_id=args.tenant_id,
            workspace_id=args.workspace_id,
            user_id=args.user_id,
            replacement_approval_id=args.replacement_approval_id,
            gate_approval_id=args.gate_approval_id,
            actor=args.actor,
            reason=getattr(args, "reason", None),
        )
    except (BrowserSkillCandidateError, SiteOpsError, FileNotFoundError, ValueError) as exc:
        return _error(args, exc)
    lines = [
        "SiteOps trusted inactive artifact writer Gate allowlist decision preflight:",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        f"  replacement_approval_id: {payload.get('replacement_approval_id')}",
        f"  gate_approval_id: {payload.get('gate_approval_id')}",
        f"  gate_allowlist_decision_preflight_status: {payload.get('gate_allowlist_decision_preflight_status')}",
        f"  approval_status: {payload.get('approval_status')}",
        f"  digest_matches: {str(payload.get('digest_matches', False)).lower()}",
        f"  ready_for_gate_policy_patch_next_pass: {str(payload.get('ready_for_gate_policy_patch_next_pass', False)).lower()}",
        "  approval_consumed: false",
        "  gate_policy_change_performed: false",
        "  allowlist_change_performed: false",
        "  inactive_artifacts_written: false",
        "  activation_allowed: false",
        "  browser_execution_allowed: false",
        "  agent_bus_enqueue_allowed: false",
        "  canonical_writeback_allowed: false",
    ]
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_trusted_inactive_artifact_writer_gate_policy_patch_plan(
    args: argparse.Namespace,
) -> int:
    """Preview exact Gate policy edits without applying them."""
    try:
        payload = candidate_promotion_trusted_inactive_artifact_writer_gate_policy_patch_plan(
            args.candidate_id,
            _vault_root_arg(args),
            tenant_id=args.tenant_id,
            workspace_id=args.workspace_id,
            user_id=args.user_id,
            replacement_approval_id=args.replacement_approval_id,
            gate_approval_id=args.gate_approval_id,
            actor=args.actor,
            reason=getattr(args, "reason", None),
        )
    except (BrowserSkillCandidateError, SiteOpsError, FileNotFoundError, ValueError) as exc:
        return _error(args, exc)
    lines = [
        "SiteOps trusted inactive artifact writer Gate policy patch plan:",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        f"  replacement_approval_id: {payload.get('replacement_approval_id')}",
        f"  gate_approval_id: {payload.get('gate_approval_id')}",
        f"  gate_policy_patch_plan_status: {payload.get('gate_policy_patch_plan_status')}",
        f"  approval_status: {payload.get('approval_status')}",
        f"  digest_matches: {str(payload.get('digest_matches', False)).lower()}",
        f"  ready_for_gate_policy_write_next_pass: {str(payload.get('ready_for_gate_policy_write_next_pass', False)).lower()}",
        "  gate_policy_change_performed: false",
        "  allowlist_change_performed: false",
        "  approval_consumed: false",
        "  inactive_artifacts_written: false",
        "  activation_allowed: false",
        "  browser_execution_allowed: false",
        "  agent_bus_enqueue_allowed: false",
        "  canonical_writeback_allowed: false",
    ]
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_trusted_inactive_artifact_writer_gate_policy_patch_application_design(
    args: argparse.Namespace,
) -> int:
    """Design the future Gate policy patch application without applying it."""
    try:
        payload = candidate_promotion_trusted_inactive_artifact_writer_gate_policy_patch_application_design(
            args.candidate_id,
            _vault_root_arg(args),
            tenant_id=args.tenant_id,
            workspace_id=args.workspace_id,
            user_id=args.user_id,
            replacement_approval_id=args.replacement_approval_id,
            gate_approval_id=args.gate_approval_id,
            actor=args.actor,
            reason=getattr(args, "reason", None),
        )
    except (BrowserSkillCandidateError, SiteOpsError, FileNotFoundError, ValueError) as exc:
        return _error(args, exc)
    lines = [
        "SiteOps trusted inactive artifact writer Gate policy patch application design:",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        f"  replacement_approval_id: {payload.get('replacement_approval_id')}",
        f"  gate_approval_id: {payload.get('gate_approval_id')}",
        f"  gate_policy_patch_application_design_status: {payload.get('gate_policy_patch_application_design_status')}",
        f"  gate_policy_patch_plan_status: {payload.get('gate_policy_patch_plan_status')}",
        f"  ready_for_gate_policy_application_next_pass: {str(payload.get('ready_for_gate_policy_application_next_pass', False)).lower()}",
        "  gate_policy_application_allowed_in_this_pass: false",
        "  gate_policy_change_performed: false",
        "  allowlist_change_performed: false",
        "  approval_consumed: false",
        "  inactive_artifacts_written: false",
        "  activation_allowed: false",
        "  browser_execution_allowed: false",
        "  agent_bus_enqueue_allowed: false",
        "  canonical_writeback_allowed: false",
    ]
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_trusted_inactive_artifact_writer_gate_policy_patch_application_preflight(
    args: argparse.Namespace,
) -> int:
    """Preflight the future Gate policy patch application without applying it."""
    try:
        payload = candidate_promotion_trusted_inactive_artifact_writer_gate_policy_patch_application_preflight(
            args.candidate_id,
            _vault_root_arg(args),
            tenant_id=args.tenant_id,
            workspace_id=args.workspace_id,
            user_id=args.user_id,
            replacement_approval_id=args.replacement_approval_id,
            gate_approval_id=args.gate_approval_id,
            actor=args.actor,
            reason=getattr(args, "reason", None),
        )
    except (BrowserSkillCandidateError, SiteOpsError, FileNotFoundError, ValueError) as exc:
        return _error(args, exc)
    lines = [
        "SiteOps trusted inactive artifact writer Gate policy patch application preflight:",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        f"  replacement_approval_id: {payload.get('replacement_approval_id')}",
        f"  gate_approval_id: {payload.get('gate_approval_id')}",
        f"  gate_policy_patch_application_preflight_status: {payload.get('gate_policy_patch_application_preflight_status')}",
        f"  gate_policy_patch_application_design_status: {payload.get('gate_policy_patch_application_design_status')}",
        f"  ready_for_gate_policy_application_write_next_pass: {str(payload.get('ready_for_gate_policy_application_write_next_pass', False)).lower()}",
        "  gate_policy_application_allowed_in_this_pass: false",
        "  gate_policy_change_performed: false",
        "  allowlist_change_performed: false",
        "  approval_consumed: false",
        "  rollback_audit_artifact_written: false",
        "  inactive_artifacts_written: false",
        "  activation_allowed: false",
        "  browser_execution_allowed: false",
        "  agent_bus_enqueue_allowed: false",
        "  canonical_writeback_allowed: false",
    ]
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_trusted_inactive_artifact_writer_gate_policy_patch_application_write_guard(
    args: argparse.Namespace,
) -> int:
    """Declare the future Gate policy patch write guard without applying it."""
    try:
        payload = candidate_promotion_trusted_inactive_artifact_writer_gate_policy_patch_application_write_guard_contract(
            args.candidate_id,
            _vault_root_arg(args),
            tenant_id=args.tenant_id,
            workspace_id=args.workspace_id,
            user_id=args.user_id,
            replacement_approval_id=args.replacement_approval_id,
            gate_approval_id=args.gate_approval_id,
            actor=args.actor,
            reason=getattr(args, "reason", None),
        )
    except (BrowserSkillCandidateError, SiteOpsError, FileNotFoundError, ValueError) as exc:
        return _error(args, exc)
    lines = [
        "SiteOps trusted inactive artifact writer Gate policy patch application write guard:",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        f"  replacement_approval_id: {payload.get('replacement_approval_id')}",
        f"  gate_approval_id: {payload.get('gate_approval_id')}",
        f"  gate_policy_patch_application_write_guard_status: {payload.get('gate_policy_patch_application_write_guard_status')}",
        f"  gate_policy_patch_application_preflight_status: {payload.get('gate_policy_patch_application_preflight_status')}",
        f"  ready_for_gate_policy_patch_writer_next_pass: {str(payload.get('ready_for_gate_policy_patch_writer_next_pass', False)).lower()}",
        "  apply_gate_policy_patch_flag_supported: false",
        "  gate_policy_patch_writer_implemented: false",
        "  gate_policy_patch_writer_allowed_in_this_pass: false",
        "  gate_policy_application_allowed_in_this_pass: false",
        "  gate_policy_change_performed: false",
        "  allowlist_change_performed: false",
        "  approval_consumed: false",
        "  rollback_audit_artifact_written: false",
        "  inactive_artifacts_written: false",
        "  activation_allowed: false",
        "  browser_execution_allowed: false",
        "  agent_bus_enqueue_allowed: false",
        "  canonical_writeback_allowed: false",
    ]
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_trusted_inactive_artifact_writer_gate_policy_patch_writer_design(
    args: argparse.Namespace,
) -> int:
    """Design the future Gate policy patch writer without building or running it."""
    try:
        payload = candidate_promotion_trusted_inactive_artifact_writer_gate_policy_patch_writer_design(
            args.candidate_id,
            _vault_root_arg(args),
            tenant_id=args.tenant_id,
            workspace_id=args.workspace_id,
            user_id=args.user_id,
            replacement_approval_id=args.replacement_approval_id,
            gate_approval_id=args.gate_approval_id,
            actor=args.actor,
            reason=getattr(args, "reason", None),
        )
    except (BrowserSkillCandidateError, SiteOpsError, FileNotFoundError, ValueError) as exc:
        return _error(args, exc)
    lines = [
        "SiteOps trusted inactive artifact writer Gate policy patch writer design:",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        f"  replacement_approval_id: {payload.get('replacement_approval_id')}",
        f"  gate_approval_id: {payload.get('gate_approval_id')}",
        f"  gate_policy_patch_writer_design_status: {payload.get('gate_policy_patch_writer_design_status')}",
        f"  gate_policy_patch_application_write_guard_status: {payload.get('gate_policy_patch_application_write_guard_status')}",
        f"  ready_for_gate_policy_patch_writer_implementation_request_next_pass: {str(payload.get('ready_for_gate_policy_patch_writer_implementation_request_next_pass', False)).lower()}",
        "  apply_gate_policy_patch_flag_supported: false",
        "  gate_policy_patch_writer_implemented: false",
        "  gate_policy_patch_writer_allowed_in_this_pass: false",
        "  gate_policy_change_performed: false",
        "  allowlist_change_performed: false",
        "  backup_artifact_written: false",
        "  rollback_audit_artifact_written: false",
        "  approval_consumed: false",
        "  inactive_artifacts_written: false",
        "  activation_allowed: false",
        "  browser_execution_allowed: false",
        "  agent_bus_enqueue_allowed: false",
        "  canonical_writeback_allowed: false",
    ]
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_trusted_inactive_artifact_writer_gate_policy_patch_writer_implementation_request(
    args: argparse.Namespace,
) -> int:
    """Return a no-write implementation request for the future Gate policy patch writer."""
    try:
        payload = candidate_promotion_trusted_inactive_artifact_writer_gate_policy_patch_writer_implementation_request(
            args.candidate_id,
            _vault_root_arg(args),
            tenant_id=args.tenant_id,
            workspace_id=args.workspace_id,
            user_id=args.user_id,
            replacement_approval_id=args.replacement_approval_id,
            gate_approval_id=args.gate_approval_id,
            actor=args.actor,
            reason=getattr(args, "reason", None),
        )
    except (BrowserSkillCandidateError, SiteOpsError, FileNotFoundError, ValueError) as exc:
        return _error(args, exc)
    lines = [
        "SiteOps trusted inactive artifact writer Gate policy patch writer implementation request:",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        f"  replacement_approval_id: {payload.get('replacement_approval_id')}",
        f"  gate_approval_id: {payload.get('gate_approval_id')}",
        f"  gate_policy_patch_writer_implementation_request_status: {payload.get('gate_policy_patch_writer_implementation_request_status')}",
        f"  gate_policy_patch_writer_design_status: {payload.get('gate_policy_patch_writer_design_status')}",
        f"  ready_for_gate_policy_patch_writer_implementation_approval_next_pass: {str(payload.get('ready_for_gate_policy_patch_writer_implementation_approval_next_pass', False)).lower()}",
        "  implementation_request_artifact_written: false",
        "  apply_gate_policy_patch_flag_supported: false",
        "  gate_policy_patch_writer_implemented: false",
        "  gate_policy_patch_writer_allowed_in_this_pass: false",
        "  gate_policy_change_performed: false",
        "  allowlist_change_performed: false",
        "  backup_artifact_written: false",
        "  rollback_audit_artifact_written: false",
        "  approval_consumed: false",
        "  inactive_artifacts_written: false",
        "  activation_allowed: false",
        "  browser_execution_allowed: false",
        "  agent_bus_enqueue_allowed: false",
        "  canonical_writeback_allowed: false",
    ]
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_trusted_inactive_artifact_writer_gate_policy_patch_writer_implementation_approval(
    args: argparse.Namespace,
) -> int:
    """Return a no-write approve/reject packet for the future Gate policy patch writer."""
    try:
        payload = (
            candidate_promotion_trusted_inactive_artifact_writer_gate_policy_patch_writer_implementation_approval(
                args.candidate_id,
                _vault_root_arg(args),
                tenant_id=args.tenant_id,
                workspace_id=args.workspace_id,
                user_id=args.user_id,
                replacement_approval_id=args.replacement_approval_id,
                gate_approval_id=args.gate_approval_id,
                decision=args.decision,
                actor=args.actor,
                reason=getattr(args, "reason", None),
            )
        )
    except (BrowserSkillCandidateError, SiteOpsError, FileNotFoundError, ValueError) as exc:
        return _error(args, exc)
    lines = [
        "SiteOps trusted inactive artifact writer Gate policy patch writer implementation approval:",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        f"  replacement_approval_id: {payload.get('replacement_approval_id')}",
        f"  gate_approval_id: {payload.get('gate_approval_id')}",
        f"  decision: {payload.get('decision')}",
        f"  actor: {payload.get('actor')}",
        "  gate_policy_patch_writer_implementation_approval_status: "
        f"{payload.get('gate_policy_patch_writer_implementation_approval_status')}",
        f"  review_decision: {payload.get('review_decision')}",
        "  gate_policy_patch_writer_implementation_allowed_next_pass: "
        f"{str(payload.get('gate_policy_patch_writer_implementation_allowed_next_pass', False)).lower()}",
        "  implementation_approval_record_written: false",
        "  apply_gate_policy_patch_flag_supported: false",
        "  gate_policy_patch_writer_implemented: false",
        "  gate_policy_patch_writer_allowed_in_this_pass: false",
        "  gate_policy_change_performed: false",
        "  allowlist_change_performed: false",
        "  backup_artifact_written: false",
        "  rollback_audit_artifact_written: false",
        "  approval_consumed: false",
        "  inactive_artifacts_written: false",
        "  activation_allowed: false",
        "  browser_execution_allowed: false",
        "  agent_bus_enqueue_allowed: false",
        "  canonical_writeback_allowed: false",
    ]
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_trusted_inactive_artifact_writer_gate_policy_patch_writer_implementation(
    args: argparse.Namespace,
) -> int:
    """Apply the guarded Gate policy patch only when --apply-gate-policy-patch is present."""
    try:
        payload = (
            candidate_promotion_trusted_inactive_artifact_writer_gate_policy_patch_writer_implementation(
                args.candidate_id,
                _vault_root_arg(args),
                tenant_id=args.tenant_id,
                workspace_id=args.workspace_id,
                user_id=args.user_id,
                replacement_approval_id=args.replacement_approval_id,
                gate_approval_id=args.gate_approval_id,
                actor=args.actor,
                reason=getattr(args, "reason", None),
                apply_gate_policy_patch=bool(getattr(args, "apply_gate_policy_patch", False)),
            )
        )
    except (BrowserSkillCandidateError, SiteOpsError, FileNotFoundError, ValueError) as exc:
        return _error(args, exc)
    lines = [
        "SiteOps trusted inactive artifact writer Gate policy patch writer implementation:",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        f"  replacement_approval_id: {payload.get('replacement_approval_id')}",
        f"  gate_approval_id: {payload.get('gate_approval_id')}",
        f"  actor: {payload.get('actor')}",
        "  gate_policy_patch_writer_implementation_status: "
        f"{payload.get('gate_policy_patch_writer_implementation_status')}",
        f"  apply_gate_policy_patch_requested: {str(payload.get('apply_gate_policy_patch_requested', False)).lower()}",
        f"  write_preconditions_ready: {str(payload.get('write_preconditions_ready', False)).lower()}",
        f"  gate_policy_change_performed: {str(payload.get('gate_policy_change_performed', False)).lower()}",
        f"  allowlist_change_performed: {str(payload.get('allowlist_change_performed', False)).lower()}",
        f"  backup_artifact_written: {str(payload.get('backup_artifact_written', False)).lower()}",
        f"  rollback_audit_artifact_written: {str(payload.get('rollback_audit_artifact_written', False)).lower()}",
        "  approval_consumed: false",
        "  inactive_artifacts_written: false",
        "  activation_allowed: false",
        "  browser_execution_allowed: false",
        "  agent_bus_enqueue_allowed: false",
        "  canonical_writeback_allowed: false",
    ]
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_trusted_inactive_artifact_writer_gate_policy_live_application_readiness(
    args: argparse.Namespace,
) -> int:
    """Return a no-write readiness packet for live Gate policy patch application."""
    try:
        payload = (
            candidate_promotion_trusted_inactive_artifact_writer_gate_policy_live_application_readiness(
                args.candidate_id,
                _vault_root_arg(args),
                tenant_id=args.tenant_id,
                workspace_id=args.workspace_id,
                user_id=args.user_id,
                actor=args.actor,
                replacement_approval_id=getattr(args, "replacement_approval_id", None),
                gate_approval_id=getattr(args, "gate_approval_id", None),
                reason=getattr(args, "reason", None),
            )
        )
    except (BrowserSkillCandidateError, SiteOpsError, FileNotFoundError, ValueError) as exc:
        return _error(args, exc)
    lines = [
        "SiteOps trusted inactive artifact writer Gate policy live application readiness:",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  replacement_approval_id: {payload.get('replacement_approval_id')}",
        f"  gate_approval_id: {payload.get('gate_approval_id')}",
        f"  actor: {payload.get('actor')}",
        "  gate_policy_live_application_readiness_status: "
        f"{payload.get('gate_policy_live_application_readiness_status')}",
        f"  review_decision: {payload.get('review_decision')}",
        "  ready_for_live_gate_policy_application: "
        f"{str(payload.get('ready_for_live_gate_policy_application', False)).lower()}",
        f"  gate_policy_already_applied: {str(payload.get('gate_policy_already_applied', False)).lower()}",
        "  gate_policy_change_performed: false",
        "  allowlist_change_performed: false",
        "  backup_artifact_written: false",
        "  rollback_audit_artifact_written: false",
        "  approval_consumed: false",
        "  inactive_artifacts_written: false",
        "  activation_allowed: false",
        "  browser_execution_allowed: false",
        "  agent_bus_enqueue_allowed: false",
        "  canonical_writeback_allowed: false",
    ]
    return _print_json_or_text(args, payload, lines)



def cmd_siteops_candidates_collision_policy_spec(args: argparse.Namespace) -> int:
    """Compute future collision/idempotency policy without writing artifacts."""
    try:
        payload = candidate_promotion_collision_policy_spec(
            args.candidate_id,
            _vault_root_arg(args),
            tenant_id=getattr(args, "tenant_id", None),
            workspace_id=getattr(args, "workspace_id", None) or DEFAULT_LOCAL_SCOPE["workspace_id"],
            user_id=getattr(args, "user_id", None),
            approval_id=args.approval_id,
        )
    except (BrowserSkillCandidateError, RuntimeError, ValueError, SiteOpsError) as exc:
        return _error(args, exc)

    lines = [
        "ChaseOS SiteOps Browser Skill Candidate Collision Policy Spec",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        f"  collision_policy_status: {payload.get('collision_policy_status')}",
        f"  collision_policy_pass: {str(payload.get('collision_policy_pass', False)).lower()}",
        f"  inactive_artifact_validator_status: {payload.get('inactive_artifact_validator_status')}",
        f"  gate_operation: {payload.get('gate_operation')}",
        "  review_decision: collision_contract_only_do_not_write_in_this_pass",
        "  overwrite_allowed: false",
        "  collision_resolution_allowed: false",
        "  inactive_artifacts_written: false",
        "  executor_implemented: false",
        "  writes_performed: false",
        "  trusted_skill_write_allowed: false",
        "  siteops_skill_card_write_allowed: false",
    ]
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_activation_boundary_readiness(args: argparse.Namespace) -> int:
    """Compute post-write activation boundary readiness without activation."""
    try:
        payload = candidate_promotion_activation_boundary_readiness(
            args.candidate_id,
            _vault_root_arg(args),
            tenant_id=getattr(args, "tenant_id", None),
            workspace_id=getattr(args, "workspace_id", None) or DEFAULT_LOCAL_SCOPE["workspace_id"],
            user_id=getattr(args, "user_id", None),
            approval_id=args.approval_id,
        )
    except (BrowserSkillCandidateError, RuntimeError, ValueError, SiteOpsError) as exc:
        return _error(args, exc)

    lines = [
        "ChaseOS SiteOps Browser Skill Candidate Activation Boundary Readiness",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        f"  activation_boundary_status: {payload.get('activation_boundary_status')}",
        f"  collision_policy_status: {payload.get('collision_policy_status')}",
        f"  inactive_artifact_validator_status: {payload.get('inactive_artifact_validator_status')}",
        f"  activation_gate_operation: {payload.get('activation_gate_operation')}",
        "  review_decision: activation_contract_only_do_not_activate_in_this_pass",
        "  activation_allowed: false",
        "  activation_performed: false",
        "  writes_performed: false",
        "  trusted_skill_write_allowed: false",
        "  siteops_skill_card_write_allowed: false",
        "  browser_execution_allowed: false",
    ]
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_activation_approval_request(args: argparse.Namespace) -> int:
    """Preview or write a pending activation approval request without activation."""
    try:
        payload = candidate_promotion_activation_approval_request(
            args.candidate_id,
            _vault_root_arg(args),
            tenant_id=getattr(args, "tenant_id", None),
            workspace_id=getattr(args, "workspace_id", None) or DEFAULT_LOCAL_SCOPE["workspace_id"],
            user_id=getattr(args, "user_id", None),
            approval_id=args.approval_id,
            actor=args.actor,
            requested_by=getattr(args, "requested_by", None),
            reason=getattr(args, "reason", None),
            write_approval_request=bool(getattr(args, "write_approval_request", False)),
        )
    except (BrowserSkillCandidateError, RuntimeError, ValueError, SiteOpsError) as exc:
        return _error(args, exc)

    lines = [
        "ChaseOS SiteOps Browser Skill Candidate Activation Approval Request",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        f"  activation_approval_request_status: {payload.get('activation_approval_request_status')}",
        f"  activation_boundary_status: {payload.get('activation_boundary_status')}",
        f"  activation_gate_operation: {payload.get('activation_gate_operation')}",
        f"  approval_request_written: {str(payload.get('approval_request_written', False)).lower()}",
        f"  approval_id: {payload.get('approval_id')}",
        f"  run_ref: {payload.get('run_ref')}",
        f"  audit_ref: {payload.get('audit_ref')}",
        "  activation_allowed: false",
        "  activation_performed: false",
        "  trusted_skill_write_allowed: false",
        "  siteops_skill_card_write_allowed: false",
        "  browser_execution_allowed: false",
        "  agent_bus_enqueue_allowed: false",
        "  canonical_writeback_allowed: false",
    ]
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_activation_approval_decision_preflight(args: argparse.Namespace) -> int:
    """Validate an activation approval request before any future activation consumer."""
    try:
        payload = candidate_promotion_activation_approval_decision_preflight(
            args.candidate_id,
            _vault_root_arg(args),
            tenant_id=getattr(args, "tenant_id", None),
            workspace_id=getattr(args, "workspace_id", None) or DEFAULT_LOCAL_SCOPE["workspace_id"],
            user_id=getattr(args, "user_id", None),
            source_approval_id=args.source_approval_id,
            activation_approval_id=args.activation_approval_id,
            actor=args.actor,
            reason=getattr(args, "reason", None),
        )
    except (BrowserSkillCandidateError, RuntimeError, ValueError, SiteOpsError) as exc:
        return _error(args, exc)

    lines = [
        "ChaseOS SiteOps Browser Skill Candidate Activation Approval Decision Preflight",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        f"  source_approval_id: {payload.get('source_approval_id')}",
        f"  activation_approval_id: {payload.get('activation_approval_id')}",
        f"  activation_approval_decision_preflight_status: {payload.get('activation_approval_decision_preflight_status')}",
        f"  approval_status: {payload.get('approval_status')}",
        f"  digest_matches: {str(payload.get('digest_matches', False)).lower()}",
        f"  ready_for_activation_consumer_next_pass: {str(payload.get('ready_for_activation_consumer_next_pass', False)).lower()}",
        "  approval_decision_written: false",
        "  approval_consumed: false",
        "  activation_allowed: false",
        "  activation_performed: false",
        "  trusted_skill_write_allowed: false",
        "  siteops_skill_card_write_allowed: false",
        "  browser_execution_allowed: false",
        "  agent_bus_enqueue_allowed: false",
        "  canonical_writeback_allowed: false",
    ]
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_activation_approval_decision_consumer_design(args: argparse.Namespace) -> int:
    """Design the future activation approval consumer without mutation."""
    try:
        payload = candidate_promotion_activation_approval_decision_consumer_design(
            args.candidate_id,
            _vault_root_arg(args),
            tenant_id=getattr(args, "tenant_id", None),
            workspace_id=getattr(args, "workspace_id", None) or DEFAULT_LOCAL_SCOPE["workspace_id"],
            user_id=getattr(args, "user_id", None),
            source_approval_id=args.source_approval_id,
            activation_approval_id=args.activation_approval_id,
            actor=args.actor,
            reason=getattr(args, "reason", None),
        )
    except (BrowserSkillCandidateError, RuntimeError, ValueError, SiteOpsError) as exc:
        return _error(args, exc)

    lines = [
        "ChaseOS SiteOps Browser Skill Candidate Activation Approval Decision Consumer Design",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        f"  source_approval_id: {payload.get('source_approval_id')}",
        f"  activation_approval_id: {payload.get('activation_approval_id')}",
        f"  activation_approval_decision_consumer_design_status: {payload.get('activation_approval_decision_consumer_design_status')}",
        f"  activation_approval_decision_preflight_status: {payload.get('activation_approval_decision_preflight_status')}",
        f"  ready_for_activation_consumer_write_guard_next_pass: {str(payload.get('ready_for_activation_consumer_write_guard_next_pass', False)).lower()}",
        "  activation_consumer_implemented: false",
        "  activation_consumption_marker_written: false",
        "  approval_consumed: false",
        "  activation_allowed: false",
        "  activation_performed: false",
        "  trusted_skill_write_allowed: false",
        "  siteops_skill_card_write_allowed: false",
        "  browser_execution_allowed: false",
        "  agent_bus_enqueue_allowed: false",
        "  canonical_writeback_allowed: false",
    ]
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_activation_approval_decision_consumer_write_guard(args: argparse.Namespace) -> int:
    """Declare the future activation approval consumer write guard without mutation."""
    if bool(getattr(args, "consume_activation_approval", False)):
        message = (
            "activation-approval-decision-consumer-write-guard is read-only; "
            "--consume-activation-approval is reserved for a future reviewed writer"
        )
        return _error(args, ValueError(message))
    try:
        payload = candidate_promotion_activation_approval_decision_consumer_write_guard_contract(
            args.candidate_id,
            _vault_root_arg(args),
            tenant_id=getattr(args, "tenant_id", None),
            workspace_id=getattr(args, "workspace_id", None) or DEFAULT_LOCAL_SCOPE["workspace_id"],
            user_id=getattr(args, "user_id", None),
            source_approval_id=args.source_approval_id,
            activation_approval_id=args.activation_approval_id,
            actor=args.actor,
            reason=getattr(args, "reason", None),
        )
    except (BrowserSkillCandidateError, RuntimeError, ValueError, SiteOpsError) as exc:
        return _error(args, exc)

    lines = [
        "ChaseOS SiteOps Browser Skill Candidate Activation Approval Decision Consumer Write Guard",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        f"  source_approval_id: {payload.get('source_approval_id')}",
        f"  activation_approval_id: {payload.get('activation_approval_id')}",
        f"  activation_approval_decision_consumer_write_guard_status: {payload.get('activation_approval_decision_consumer_write_guard_status')}",
        f"  activation_approval_decision_consumer_design_status: {payload.get('activation_approval_decision_consumer_design_status')}",
        f"  ready_for_activation_consumer_writer_design_next_pass: {str(payload.get('ready_for_activation_consumer_writer_design_next_pass', False)).lower()}",
        "  consume_activation_approval_flag_supported: false",
        "  activation_consumer_writer_implemented: false",
        "  activation_consumption_marker_written: false",
        "  approval_consumed: false",
        "  activation_allowed: false",
        "  activation_performed: false",
        "  trusted_skill_write_allowed: false",
        "  siteops_skill_card_write_allowed: false",
        "  browser_execution_allowed: false",
        "  agent_bus_enqueue_allowed: false",
        "  canonical_writeback_allowed: false",
    ]
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_activation_approval_decision_consumer_writer_design(args: argparse.Namespace) -> int:
    """Design the future activation approval consumer writer without mutation."""
    try:
        payload = candidate_promotion_activation_approval_decision_consumer_writer_design(
            args.candidate_id,
            _vault_root_arg(args),
            tenant_id=getattr(args, "tenant_id", None),
            workspace_id=getattr(args, "workspace_id", None) or DEFAULT_LOCAL_SCOPE["workspace_id"],
            user_id=getattr(args, "user_id", None),
            source_approval_id=args.source_approval_id,
            activation_approval_id=args.activation_approval_id,
            actor=args.actor,
            reason=getattr(args, "reason", None),
        )
    except (BrowserSkillCandidateError, RuntimeError, ValueError, SiteOpsError) as exc:
        return _error(args, exc)

    lines = [
        "ChaseOS SiteOps Browser Skill Candidate Activation Approval Decision Consumer Writer Design",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        f"  source_approval_id: {payload.get('source_approval_id')}",
        f"  activation_approval_id: {payload.get('activation_approval_id')}",
        f"  activation_approval_decision_consumer_writer_design_status: {payload.get('activation_approval_decision_consumer_writer_design_status')}",
        f"  activation_approval_decision_consumer_write_guard_status: {payload.get('activation_approval_decision_consumer_write_guard_status')}",
        f"  ready_for_activation_consumer_writer_implementation_request_next_pass: {str(payload.get('ready_for_activation_consumer_writer_implementation_request_next_pass', False)).lower()}",
        "  consume_activation_approval_flag_supported: false",
        "  activation_consumer_writer_implemented: false",
        "  activation_consumption_marker_written: false",
        "  approval_consumed: false",
        "  activation_allowed: false",
        "  activation_performed: false",
        "  trusted_skill_write_allowed: false",
        "  siteops_skill_card_write_allowed: false",
        "  browser_execution_allowed: false",
        "  agent_bus_enqueue_allowed: false",
        "  canonical_writeback_allowed: false",
    ]
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_activation_approval_decision_consumer_writer_implementation_request(
    args: argparse.Namespace,
) -> int:
    """Package the future activation approval consumer writer implementation request without mutation."""
    if bool(getattr(args, "consume_activation_approval", False)):
        message = (
            "activation-approval-decision-consumer-writer-implementation-request is read-only; "
            "--consume-activation-approval is reserved for a future reviewed writer implementation"
        )
        return _error(args, ValueError(message))
    try:
        payload = candidate_promotion_activation_approval_decision_consumer_writer_implementation_request(
            args.candidate_id,
            _vault_root_arg(args),
            tenant_id=getattr(args, "tenant_id", None),
            workspace_id=getattr(args, "workspace_id", None) or DEFAULT_LOCAL_SCOPE["workspace_id"],
            user_id=getattr(args, "user_id", None),
            source_approval_id=args.source_approval_id,
            activation_approval_id=args.activation_approval_id,
            actor=args.actor,
            reason=getattr(args, "reason", None),
        )
    except (BrowserSkillCandidateError, RuntimeError, ValueError, SiteOpsError) as exc:
        return _error(args, exc)

    lines = [
        "ChaseOS SiteOps Browser Skill Candidate Activation Approval Decision Consumer Writer Implementation Request",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        f"  source_approval_id: {payload.get('source_approval_id')}",
        f"  activation_approval_id: {payload.get('activation_approval_id')}",
        f"  activation_approval_decision_consumer_writer_implementation_request_status: {payload.get('activation_approval_decision_consumer_writer_implementation_request_status')}",
        f"  activation_approval_decision_consumer_writer_design_status: {payload.get('activation_approval_decision_consumer_writer_design_status')}",
        f"  ready_for_activation_consumer_writer_implementation_approval_next_pass: {str(payload.get('ready_for_activation_consumer_writer_implementation_approval_next_pass', False)).lower()}",
        "  consume_activation_approval_flag_supported: false",
        "  implementation_request_artifact_written: false",
        "  activation_consumer_writer_implemented: false",
        "  activation_consumption_marker_written: false",
        "  approval_consumed: false",
        "  activation_allowed: false",
        "  activation_performed: false",
        "  trusted_skill_write_allowed: false",
        "  siteops_skill_card_write_allowed: false",
        "  browser_execution_allowed: false",
        "  agent_bus_enqueue_allowed: false",
        "  canonical_writeback_allowed: false",
    ]
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_activation_approval_decision_consumer_writer_implementation_approval(
    args: argparse.Namespace,
) -> int:
    """Return approve/reject intent for the future activation approval consumer writer."""
    if bool(getattr(args, "consume_activation_approval", False)):
        message = (
            "activation-approval-decision-consumer-writer-implementation-approval is read-only; "
            "--consume-activation-approval is reserved for a future reviewed writer implementation"
        )
        return _error(args, ValueError(message))
    try:
        payload = candidate_promotion_activation_approval_decision_consumer_writer_implementation_approval(
            args.candidate_id,
            _vault_root_arg(args),
            tenant_id=getattr(args, "tenant_id", None),
            workspace_id=getattr(args, "workspace_id", None) or DEFAULT_LOCAL_SCOPE["workspace_id"],
            user_id=getattr(args, "user_id", None),
            source_approval_id=args.source_approval_id,
            activation_approval_id=args.activation_approval_id,
            decision=args.decision,
            actor=args.actor,
            reason=getattr(args, "reason", None),
        )
    except (BrowserSkillCandidateError, RuntimeError, ValueError, SiteOpsError) as exc:
        return _error(args, exc)

    lines = [
        "ChaseOS SiteOps Browser Skill Candidate Activation Approval Decision Consumer Writer Implementation Approval",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        f"  source_approval_id: {payload.get('source_approval_id')}",
        f"  activation_approval_id: {payload.get('activation_approval_id')}",
        f"  decision: {payload.get('decision')}",
        f"  activation_approval_decision_consumer_writer_implementation_approval_status: {payload.get('activation_approval_decision_consumer_writer_implementation_approval_status')}",
        f"  activation_approval_decision_consumer_writer_implementation_request_status: {payload.get('activation_approval_decision_consumer_writer_implementation_request_status')}",
        f"  ready_for_activation_consumer_writer_implementation_next_pass: {str(payload.get('ready_for_activation_consumer_writer_implementation_next_pass', False)).lower()}",
        "  consume_activation_approval_flag_supported: false",
        "  implementation_approval_artifact_written: false",
        "  activation_consumer_writer_implemented: false",
        "  activation_consumption_marker_written: false",
        "  approval_consumed: false",
        "  activation_allowed: false",
        "  activation_performed: false",
        "  trusted_skill_write_allowed: false",
        "  siteops_skill_card_write_allowed: false",
        "  browser_execution_allowed: false",
        "  agent_bus_enqueue_allowed: false",
        "  canonical_writeback_allowed: false",
    ]
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_activation_approval_decision_consumer_writer_implementation(
    args: argparse.Namespace,
) -> int:
    """Run the guarded activation approval consumer writer implementation."""
    try:
        payload = candidate_promotion_activation_approval_decision_consumer_writer_implementation(
            args.candidate_id,
            _vault_root_arg(args),
            tenant_id=getattr(args, "tenant_id", None),
            workspace_id=getattr(args, "workspace_id", None) or DEFAULT_LOCAL_SCOPE["workspace_id"],
            user_id=getattr(args, "user_id", None),
            source_approval_id=args.source_approval_id,
            activation_approval_id=args.activation_approval_id,
            actor=args.actor,
            reason=getattr(args, "reason", None),
            consume_activation_approval=bool(getattr(args, "consume_activation_approval", False)),
        )
    except (BrowserSkillCandidateError, RuntimeError, ValueError, SiteOpsError) as exc:
        return _error(args, exc)

    lines = [
        "ChaseOS SiteOps Browser Skill Candidate Activation Approval Decision Consumer Writer Implementation",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        f"  source_approval_id: {payload.get('source_approval_id')}",
        f"  activation_approval_id: {payload.get('activation_approval_id')}",
        f"  activation_approval_decision_consumer_writer_implementation_status: {payload.get('activation_approval_decision_consumer_writer_implementation_status')}",
        f"  consume_activation_approval_requested: {str(payload.get('consume_activation_approval_requested', False)).lower()}",
        f"  activation_consumer_writer_ready_to_consume: {str(payload.get('activation_consumer_writer_ready_to_consume', False)).lower()}",
        f"  activation_consumption_marker_written: {str(payload.get('activation_consumption_marker_written', False)).lower()}",
        f"  activation_consumer_audit_written: {str(payload.get('activation_consumer_audit_written', False)).lower()}",
        f"  approval_consumed: {str(payload.get('approval_consumed', False)).lower()}",
        "  activation_allowed: false",
        "  activation_performed: false",
        "  trusted_skill_write_allowed: false",
        "  siteops_skill_card_write_allowed: false",
        "  browser_execution_allowed: false",
        "  agent_bus_enqueue_allowed: false",
        "  canonical_writeback_allowed: false",
    ]
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_activation_consumption_live_readiness(args: argparse.Namespace) -> int:
    """Report whether activation approval consumption is ready without writing."""
    try:
        payload = candidate_promotion_activation_consumption_live_readiness(
            args.candidate_id,
            _vault_root_arg(args),
            tenant_id=getattr(args, "tenant_id", None),
            workspace_id=getattr(args, "workspace_id", None) or DEFAULT_LOCAL_SCOPE["workspace_id"],
            user_id=getattr(args, "user_id", None),
            actor=args.actor,
            source_approval_id=getattr(args, "source_approval_id", None),
            activation_approval_id=getattr(args, "activation_approval_id", None),
            reason=getattr(args, "reason", None),
        )
    except (BrowserSkillCandidateError, RuntimeError, ValueError, SiteOpsError) as exc:
        return _error(args, exc)

    lines = [
        "ChaseOS SiteOps Browser Skill Candidate Activation Consumption Live Readiness",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        f"  source_approval_id: {payload.get('source_approval_id')}",
        f"  activation_approval_id: {payload.get('activation_approval_id')}",
        f"  activation_consumption_live_readiness_status: {payload.get('activation_consumption_live_readiness_status')}",
        f"  writer_dry_run_ready: {str(payload.get('writer_dry_run_ready', False)).lower()}",
        "  activation_consumption_marker_written: false",
        "  activation_consumer_audit_written: false",
        "  approval_consumed: false",
        "  activation_allowed: false",
        "  activation_performed: false",
        "  trusted_skill_write_allowed: false",
        "  browser_execution_allowed: false",
        "  agent_bus_enqueue_allowed: false",
        "  canonical_writeback_allowed: false",
    ]
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_activation_executor_design(args: argparse.Namespace) -> int:
    """Design the future activation executor without mutation or browser execution."""
    try:
        payload = candidate_promotion_activation_executor_design(
            args.candidate_id,
            _vault_root_arg(args),
            tenant_id=getattr(args, "tenant_id", None),
            workspace_id=getattr(args, "workspace_id", None),
            user_id=getattr(args, "user_id", None),
            source_approval_id=args.source_approval_id,
            activation_approval_id=args.activation_approval_id,
            actor=args.actor,
            reason=getattr(args, "reason", None),
        )
    except (SiteOpsError, BrowserSkillCandidateError, RuntimeError, ValueError) as exc:
        return _error(args, exc)
    lines = [
        "ChaseOS SiteOps Candidate Activation Executor Design",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        f"  source_approval_id: {payload.get('source_approval_id')}",
        f"  activation_approval_id: {payload.get('activation_approval_id')}",
        f"  activation_executor_design_status: {payload.get('activation_executor_design_status')}",
        f"  ready_for_activation_executor_preflight_next_pass: {str(payload.get('ready_for_activation_executor_preflight_next_pass', False)).lower()}",
        "  activation_performed: false",
        "  browser_execution_allowed: false",
        "  canonical_writeback_allowed: false",
    ]
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_activation_executor_preflight(args: argparse.Namespace) -> int:
    """Preflight the future activation executor without mutation or browser execution."""
    try:
        payload = candidate_promotion_activation_executor_preflight(
            args.candidate_id,
            _vault_root_arg(args),
            tenant_id=getattr(args, "tenant_id", None),
            workspace_id=getattr(args, "workspace_id", None),
            user_id=getattr(args, "user_id", None),
            source_approval_id=args.source_approval_id,
            activation_approval_id=args.activation_approval_id,
            actor=args.actor,
            reason=getattr(args, "reason", None),
        )
    except (SiteOpsError, BrowserSkillCandidateError, RuntimeError, ValueError) as exc:
        return _error(args, exc)
    lines = [
        "ChaseOS SiteOps Candidate Activation Executor Preflight",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        f"  source_approval_id: {payload.get('source_approval_id')}",
        f"  activation_approval_id: {payload.get('activation_approval_id')}",
        f"  activation_executor_preflight_status: {payload.get('activation_executor_preflight_status')}",
        f"  ready_for_activation_executor_implementation_request_next_pass: {str(payload.get('ready_for_activation_executor_implementation_request_next_pass', False)).lower()}",
        "  activation_record_written: false",
        "  activation_performed: false",
        "  trusted_artifacts_mutated: false",
        "  browser_execution_allowed: false",
        "  canonical_writeback_allowed: false",
    ]
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_activation_executor_implementation_request(args: argparse.Namespace) -> int:
    """Package activation executor preflight evidence for operator review without writes."""
    try:
        payload = candidate_promotion_activation_executor_implementation_request(
            args.candidate_id,
            _vault_root_arg(args),
            tenant_id=getattr(args, "tenant_id", None),
            workspace_id=getattr(args, "workspace_id", None),
            user_id=getattr(args, "user_id", None),
            source_approval_id=args.source_approval_id,
            activation_approval_id=args.activation_approval_id,
            actor=args.actor,
            reason=getattr(args, "reason", None),
        )
    except (SiteOpsError, BrowserSkillCandidateError, RuntimeError, ValueError) as exc:
        return _error(args, exc)
    lines = [
        "ChaseOS SiteOps Candidate Activation Executor Implementation Request",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        f"  source_approval_id: {payload.get('source_approval_id')}",
        f"  activation_approval_id: {payload.get('activation_approval_id')}",
        f"  activation_executor_implementation_request_status: {payload.get('activation_executor_implementation_request_status')}",
        f"  ready_for_activation_executor_implementation_approval_next_pass: {str(payload.get('ready_for_activation_executor_implementation_approval_next_pass', False)).lower()}",
        "  implementation_request_artifact_written: false",
        "  activation_record_written: false",
        "  activation_performed: false",
        "  trusted_artifacts_mutated: false",
        "  browser_execution_allowed: false",
        "  canonical_writeback_allowed: false",
    ]
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_activation_executor_implementation_approval(args: argparse.Namespace) -> int:
    """Return no-write approve/reject intent for future activation executor implementation."""
    try:
        payload = candidate_promotion_activation_executor_implementation_approval(
            args.candidate_id,
            _vault_root_arg(args),
            tenant_id=getattr(args, "tenant_id", None),
            workspace_id=getattr(args, "workspace_id", None),
            user_id=getattr(args, "user_id", None),
            source_approval_id=args.source_approval_id,
            activation_approval_id=args.activation_approval_id,
            decision=args.decision,
            actor=args.actor,
            reason=getattr(args, "reason", None),
        )
    except (SiteOpsError, BrowserSkillCandidateError, RuntimeError, ValueError) as exc:
        return _error(args, exc)
    lines = [
        "ChaseOS SiteOps Candidate Activation Executor Implementation Approval",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        f"  decision: {payload.get('decision')}",
        f"  source_approval_id: {payload.get('source_approval_id')}",
        f"  activation_approval_id: {payload.get('activation_approval_id')}",
        f"  activation_executor_implementation_approval_status: {payload.get('activation_executor_implementation_approval_status')}",
        f"  ready_for_activation_executor_implementation_next_pass: {str(payload.get('ready_for_activation_executor_implementation_next_pass', False)).lower()}",
        "  implementation_approval_artifact_written: false",
        "  activation_record_written: false",
        "  activation_performed: false",
        "  trusted_artifacts_mutated: false",
        "  browser_execution_allowed: false",
        "  canonical_writeback_allowed: false",
    ]
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_activation_executor_implementation(args: argparse.Namespace) -> int:
    """Run the guarded activation executor implementation."""
    try:
        payload = candidate_promotion_activation_executor_implementation(
            args.candidate_id,
            _vault_root_arg(args),
            tenant_id=getattr(args, "tenant_id", None),
            workspace_id=getattr(args, "workspace_id", None),
            user_id=getattr(args, "user_id", None),
            source_approval_id=args.source_approval_id,
            activation_approval_id=args.activation_approval_id,
            actor=args.actor,
            reason=getattr(args, "reason", None),
            activate_trusted_artifact=bool(getattr(args, "activate_trusted_artifact", False)),
        )
    except (SiteOpsError, BrowserSkillCandidateError, RuntimeError, ValueError) as exc:
        return _error(args, exc)
    lines = [
        "ChaseOS SiteOps Candidate Activation Executor Implementation",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        f"  source_approval_id: {payload.get('source_approval_id')}",
        f"  activation_approval_id: {payload.get('activation_approval_id')}",
        f"  activation_executor_implementation_status: {payload.get('activation_executor_implementation_status')}",
        f"  activate_trusted_artifact_requested: {str(payload.get('activate_trusted_artifact_requested', False)).lower()}",
        f"  activation_record_written: {str(payload.get('activation_record_written', False)).lower()}",
        f"  activation_performed: {str(payload.get('activation_performed', False)).lower()}",
        f"  trusted_artifacts_mutated: {str(payload.get('trusted_artifacts_mutated', False)).lower()}",
        "  browser_execution_allowed: false",
        "  canonical_writeback_allowed: false",
    ]
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_activation_executor_live_readiness(args: argparse.Namespace) -> int:
    """Report activation executor live readiness without writing or activating."""
    try:
        payload = candidate_promotion_activation_executor_live_readiness(
            args.candidate_id,
            _vault_root_arg(args),
            tenant_id=getattr(args, "tenant_id", None),
            workspace_id=getattr(args, "workspace_id", None),
            user_id=getattr(args, "user_id", None),
            actor=args.actor,
            source_approval_id=getattr(args, "source_approval_id", None),
            activation_approval_id=getattr(args, "activation_approval_id", None),
            reason=getattr(args, "reason", None),
        )
    except (SiteOpsError, BrowserSkillCandidateError, RuntimeError, ValueError) as exc:
        return _error(args, exc)
    lines = [
        "ChaseOS SiteOps Candidate Activation Executor Live Readiness",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        f"  source_approval_id: {payload.get('source_approval_id')}",
        f"  activation_approval_id: {payload.get('activation_approval_id')}",
        f"  activation_executor_live_readiness_status: {payload.get('activation_executor_live_readiness_status')}",
        f"  activation_executor_dry_run_status: {payload.get('activation_executor_dry_run_status')}",
        f"  gate_operation_allowed: {str(payload.get('gate_operation_allowed', False)).lower()}",
        f"  activation_record_exists: {str(payload.get('activation_record_exists', False)).lower()}",
        "  activation_record_written: false",
        "  activation_performed: false",
        "  trusted_artifacts_mutated: false",
        "  browser_execution_allowed: false",
        "  canonical_writeback_allowed: false",
    ]
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_activation_gate_live_readiness(args: argparse.Namespace) -> int:
    """Report activation Gate live readiness without mutating Gate policy."""
    try:
        payload = candidate_promotion_activation_gate_live_readiness(
            args.candidate_id,
            _vault_root_arg(args),
            tenant_id=getattr(args, "tenant_id", None),
            workspace_id=getattr(args, "workspace_id", None),
            user_id=getattr(args, "user_id", None),
            source_approval_id=getattr(args, "source_approval_id", None),
            activation_approval_id=getattr(args, "activation_approval_id", None),
            actor=args.actor,
            reason=getattr(args, "reason", None),
        )
    except (BrowserSkillCandidateError, SiteOpsError, RuntimeError, ValueError) as exc:
        return _error(args, exc)
    lines = [
        "SiteOps activation Gate live readiness:",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        f"  source_approval_id: {payload.get('source_approval_id')}",
        f"  activation_approval_id: {payload.get('activation_approval_id')}",
        f"  activation_gate_live_readiness_status: {payload.get('activation_gate_live_readiness_status')}",
        f"  gate_operation: {payload.get('gate_operation')}",
        f"  gate_operation_allowed: {str(payload.get('gate_operation_allowed', False)).lower()}",
        "  ready_for_activation_gate_policy_patch_plan: "
        f"{str(payload.get('ready_for_activation_gate_policy_patch_plan', False)).lower()}",
        "  gate_policy_change_performed: false",
        "  allowlist_change_performed: false",
        "  activation_record_written: false",
        "  activation_performed: false",
        "  browser_execution_allowed: false",
        "  agent_bus_enqueue_allowed: false",
        "  canonical_writeback_allowed: false",
    ]
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_activation_gate_policy_patch_writer_implementation(
    args: argparse.Namespace,
) -> int:
    """Apply the activation Gate policy patch only with explicit approval and flag."""
    try:
        payload = candidate_promotion_activation_gate_policy_patch_writer_implementation(
            args.candidate_id,
            _vault_root_arg(args),
            tenant_id=getattr(args, "tenant_id", None),
            workspace_id=getattr(args, "workspace_id", None),
            user_id=getattr(args, "user_id", None),
            source_approval_id=args.source_approval_id,
            activation_approval_id=args.activation_approval_id,
            actor=args.actor,
            reason=getattr(args, "reason", None),
            apply_activation_gate_policy_patch=bool(
                getattr(args, "apply_activation_gate_policy_patch", False)
            ),
        )
    except (SiteOpsError, BrowserSkillCandidateError, RuntimeError, ValueError) as exc:
        return _error(args, exc)
    lines = [
        "ChaseOS SiteOps Candidate Activation Gate Policy Patch Writer Implementation",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        f"  source_approval_id: {payload.get('source_approval_id')}",
        f"  activation_approval_id: {payload.get('activation_approval_id')}",
        "  activation_gate_policy_patch_writer_implementation_status: "
        f"{payload.get('activation_gate_policy_patch_writer_implementation_status')}",
        "  apply_activation_gate_policy_patch_requested: "
        f"{str(payload.get('apply_activation_gate_policy_patch_requested', False)).lower()}",
        f"  write_preconditions_ready: {str(payload.get('write_preconditions_ready', False)).lower()}",
        f"  gate_policy_change_performed: {str(payload.get('gate_policy_change_performed', False)).lower()}",
        f"  allowlist_change_performed: {str(payload.get('allowlist_change_performed', False)).lower()}",
        f"  activation_record_written: {str(payload.get('activation_record_written', False)).lower()}",
        f"  activation_performed: {str(payload.get('activation_performed', False)).lower()}",
        "  browser_execution_allowed: false",
        "  agent_bus_enqueue_allowed: false",
        "  canonical_writeback_allowed: false",
    ]
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_live_activation_evidence_closeout(args: argparse.Namespace) -> int:
    """Summarize live activation evidence blockers without writing or activating."""
    try:
        payload = candidate_promotion_live_activation_evidence_closeout(
            args.candidate_id,
            _vault_root_arg(args),
            tenant_id=getattr(args, "tenant_id", None),
            workspace_id=getattr(args, "workspace_id", None),
            user_id=getattr(args, "user_id", None),
            actor=args.actor,
            source_approval_id=getattr(args, "source_approval_id", None),
            activation_approval_id=getattr(args, "activation_approval_id", None),
            reason=getattr(args, "reason", None),
        )
    except (SiteOpsError, BrowserSkillCandidateError, RuntimeError, ValueError) as exc:
        return _error(args, exc)
    lines = [
        "ChaseOS SiteOps Candidate Live Activation Evidence Closeout",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        f"  live_activation_evidence_closeout_status: {payload.get('live_activation_evidence_closeout_status')}",
        f"  backend_activation_ready: {str(payload.get('backend_activation_ready', False)).lower()}",
        f"  browser_replay_built: {str(payload.get('browser_replay_built', False)).lower()}",
        f"  feature_done: {str(payload.get('feature_done', False)).lower()}",
        f"  remaining_backend_activation_blockers: {', '.join(payload.get('remaining_backend_activation_blockers') or [])}",
        f"  remaining_feature_blockers: {', '.join(payload.get('remaining_feature_blockers') or [])}",
        "  activation_performed: false",
        "  browser_execution_allowed: false",
        "  canonical_writeback_allowed: false",
    ]
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_browser_skill_shadow_replay_design(args: argparse.Namespace) -> int:
    """Design Browser Skill shadow replay boundaries without browser execution."""
    try:
        payload = candidate_promotion_browser_skill_shadow_replay_design(
            args.candidate_id,
            _vault_root_arg(args),
            tenant_id=getattr(args, "tenant_id", None),
            workspace_id=getattr(args, "workspace_id", None),
            user_id=getattr(args, "user_id", None),
            actor=args.actor,
            source_approval_id=getattr(args, "source_approval_id", None),
            activation_approval_id=getattr(args, "activation_approval_id", None),
            reason=getattr(args, "reason", None),
        )
    except (SiteOpsError, BrowserSkillCandidateError, RuntimeError, ValueError) as exc:
        return _error(args, exc)
    lines = [
        "ChaseOS SiteOps Browser Skill Shadow Replay Design",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        "  browser_skill_shadow_replay_design_status: "
        f"{payload.get('browser_skill_shadow_replay_design_status')}",
        f"  backend_activation_ready: {str(payload.get('backend_activation_ready', False)).lower()}",
        "  ready_for_shadow_replay_implementation_request_next_pass: "
        f"{str(payload.get('ready_for_shadow_replay_implementation_request_next_pass', False)).lower()}",
        f"  shadow_mode_required: {str(payload.get('shadow_mode_required', False)).lower()}",
        f"  browser_replay_built: {str(payload.get('browser_replay_built', False)).lower()}",
        "  activation_performed: false",
        "  browser_execution_allowed: false",
        "  cdp_connection_allowed: false",
        "  authenticated_session_allowed: false",
        "  canonical_writeback_allowed: false",
    ]
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_browser_skill_shadow_replay_implementation_request(
    args: argparse.Namespace,
) -> int:
    """Package Browser Skill shadow replay implementation requirements without execution."""
    try:
        payload = candidate_promotion_browser_skill_shadow_replay_implementation_request(
            args.candidate_id,
            _vault_root_arg(args),
            tenant_id=getattr(args, "tenant_id", None),
            workspace_id=getattr(args, "workspace_id", None),
            user_id=getattr(args, "user_id", None),
            actor=args.actor,
            source_approval_id=getattr(args, "source_approval_id", None),
            activation_approval_id=getattr(args, "activation_approval_id", None),
            reason=getattr(args, "reason", None),
        )
    except (SiteOpsError, BrowserSkillCandidateError, RuntimeError, ValueError) as exc:
        return _error(args, exc)
    lines = [
        "ChaseOS SiteOps Browser Skill Shadow Replay Implementation Request",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        "  browser_skill_shadow_replay_implementation_request_status: "
        f"{payload.get('browser_skill_shadow_replay_implementation_request_status')}",
        "  ready_for_shadow_replay_implementation_approval_next_pass: "
        f"{str(payload.get('ready_for_shadow_replay_implementation_approval_next_pass', False)).lower()}",
        f"  backend_activation_ready: {str(payload.get('backend_activation_ready', False)).lower()}",
        f"  shadow_mode_required: {str(payload.get('shadow_mode_required', False)).lower()}",
        f"  browser_replay_built: {str(payload.get('browser_replay_built', False)).lower()}",
        "  implementation_request_artifact_written: false",
        "  browser_run_log_written: false",
        "  activation_performed: false",
        "  browser_execution_allowed: false",
        "  cdp_connection_allowed: false",
        "  authenticated_session_allowed: false",
        "  canonical_writeback_allowed: false",
    ]
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_browser_skill_shadow_replay_implementation_approval(
    args: argparse.Namespace,
) -> int:
    """Return no-write approve/reject intent for future shadow replay implementation."""
    try:
        payload = candidate_promotion_browser_skill_shadow_replay_implementation_approval(
            args.candidate_id,
            _vault_root_arg(args),
            tenant_id=getattr(args, "tenant_id", None),
            workspace_id=getattr(args, "workspace_id", None),
            user_id=getattr(args, "user_id", None),
            actor=args.actor,
            decision=args.decision,
            source_approval_id=getattr(args, "source_approval_id", None),
            activation_approval_id=getattr(args, "activation_approval_id", None),
            reason=getattr(args, "reason", None),
        )
    except (SiteOpsError, BrowserSkillCandidateError, RuntimeError, ValueError) as exc:
        return _error(args, exc)
    lines = [
        "ChaseOS SiteOps Browser Skill Shadow Replay Implementation Approval",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        f"  decision: {payload.get('decision')}",
        "  browser_skill_shadow_replay_implementation_approval_status: "
        f"{payload.get('browser_skill_shadow_replay_implementation_approval_status')}",
        "  ready_for_shadow_replay_implementation_next_pass: "
        f"{str(payload.get('ready_for_shadow_replay_implementation_next_pass', False)).lower()}",
        "  implementation_approval_artifact_written: false",
        "  browser_run_log_written: false",
        "  activation_performed: false",
        "  browser_execution_allowed: false",
        "  cdp_connection_allowed: false",
        "  authenticated_session_allowed: false",
        "  canonical_writeback_allowed: false",
    ]
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_browser_skill_shadow_replay_runner_write_guard(
    args: argparse.Namespace,
) -> int:
    """Return future shadow replay runner write guards without browser control."""
    try:
        payload = candidate_promotion_browser_skill_shadow_replay_runner_write_guard(
            args.candidate_id,
            _vault_root_arg(args),
            tenant_id=getattr(args, "tenant_id", None),
            workspace_id=getattr(args, "workspace_id", None),
            user_id=getattr(args, "user_id", None),
            actor=args.actor,
            source_approval_id=getattr(args, "source_approval_id", None),
            activation_approval_id=getattr(args, "activation_approval_id", None),
            reason=getattr(args, "reason", None),
        )
    except (SiteOpsError, BrowserSkillCandidateError, RuntimeError, ValueError) as exc:
        return _error(args, exc)
    lines = [
        "ChaseOS SiteOps Browser Skill Shadow Replay Runner Write Guard",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        "  browser_skill_shadow_replay_runner_write_guard_status: "
        f"{payload.get('browser_skill_shadow_replay_runner_write_guard_status')}",
        "  ready_for_shadow_replay_runner_implementation_next_pass: "
        f"{str(payload.get('ready_for_shadow_replay_runner_implementation_next_pass', False)).lower()}",
        f"  backend_activation_ready: {str(payload.get('backend_activation_ready', False)).lower()}",
        f"  browser_replay_built: {str(payload.get('browser_replay_built', False)).lower()}",
        "  shadow_replay_runner_write_guard_artifact_written: false",
        "  browser_run_log_written: false",
        "  activation_performed: false",
        "  browser_execution_allowed: false",
        "  cdp_connection_allowed: false",
        "  authenticated_session_allowed: false",
        "  canonical_writeback_allowed: false",
    ]
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_browser_skill_shadow_replay_runner_implementation_dry_run(
    args: argparse.Namespace,
) -> int:
    """Plan the future shadow replay runner without browser control or writes."""
    try:
        payload = candidate_promotion_browser_skill_shadow_replay_runner_implementation_dry_run(
            args.candidate_id,
            _vault_root_arg(args),
            tenant_id=getattr(args, "tenant_id", None),
            workspace_id=getattr(args, "workspace_id", None),
            user_id=getattr(args, "user_id", None),
            actor=args.actor,
            target_url=args.target_url,
            shadow_mode=bool(getattr(args, "shadow_mode", False)),
            write_browser_run_log=bool(getattr(args, "write_browser_run_log", False)),
            local_target_only=bool(getattr(args, "local_target_only", False)),
            allowlisted_domain=getattr(args, "allowlisted_domain", None),
            max_steps=getattr(args, "max_steps", 5),
            source_approval_id=getattr(args, "source_approval_id", None),
            activation_approval_id=getattr(args, "activation_approval_id", None),
            reason=getattr(args, "reason", None),
        )
    except (SiteOpsError, BrowserSkillCandidateError, RuntimeError, ValueError) as exc:
        return _error(args, exc)
    lines = [
        "ChaseOS SiteOps Browser Skill Shadow Replay Runner Implementation Dry Run",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        "  browser_skill_shadow_replay_runner_dry_run_status: "
        f"{payload.get('browser_skill_shadow_replay_runner_dry_run_status')}",
        "  ready_for_shadow_replay_runner_write_pass_next: "
        f"{str(payload.get('ready_for_shadow_replay_runner_write_pass_next', False)).lower()}",
        f"  target_url: {payload.get('target_url')}",
        f"  target_policy_reason: {payload.get('target_policy_reason')}",
        f"  runner_dry_run_shell_built: {str(payload.get('runner_dry_run_shell_built', False)).lower()}",
        f"  browser_replay_built: {str(payload.get('browser_replay_built', False)).lower()}",
        "  browser_run_log_written: false",
        "  runner_dry_run_artifact_written: false",
        "  browser_execution_allowed: false",
        "  cdp_connection_allowed: false",
        "  authenticated_session_allowed: false",
        "  canonical_writeback_allowed: false",
    ]
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_browser_skill_shadow_replay_runner_write_pass(
    args: argparse.Namespace,
) -> int:
    """Write scoped shadow replay dry-run evidence only when explicitly requested."""
    try:
        payload = candidate_promotion_browser_skill_shadow_replay_runner_write_pass(
            args.candidate_id,
            _vault_root_arg(args),
            tenant_id=getattr(args, "tenant_id", None),
            workspace_id=getattr(args, "workspace_id", None),
            user_id=getattr(args, "user_id", None),
            actor=args.actor,
            target_url=args.target_url,
            shadow_mode=bool(getattr(args, "shadow_mode", False)),
            write_browser_run_log=bool(getattr(args, "write_browser_run_log", False)),
            local_target_only=bool(getattr(args, "local_target_only", False)),
            allowlisted_domain=getattr(args, "allowlisted_domain", None),
            max_steps=getattr(args, "max_steps", 5),
            source_approval_id=getattr(args, "source_approval_id", None),
            activation_approval_id=getattr(args, "activation_approval_id", None),
            reason=getattr(args, "reason", None),
        )
    except (SiteOpsError, BrowserSkillCandidateError, RuntimeError, ValueError) as exc:
        return _error(args, exc)
    lines = [
        "ChaseOS SiteOps Browser Skill Shadow Replay Runner Write Pass",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        "  browser_skill_shadow_replay_runner_write_pass_status: "
        f"{payload.get('browser_skill_shadow_replay_runner_write_pass_status')}",
        "  write_browser_run_log_requested: "
        f"{str(payload.get('write_browser_run_log_requested', False)).lower()}",
        f"  browser_run_log_written: {str(payload.get('browser_run_log_written', False)).lower()}",
        f"  agent_activity_log_written: {str(payload.get('agent_activity_log_written', False)).lower()}",
        f"  candidate_evidence_written: {str(payload.get('candidate_evidence_written', False)).lower()}",
        f"  browser_run_ref: {payload.get('browser_run_ref')}",
        f"  agent_activity_ref: {payload.get('agent_activity_ref')}",
        f"  candidate_evidence_ref: {payload.get('candidate_evidence_ref')}",
        "  ready_for_replay_evidence_review_next: "
        f"{str(payload.get('ready_for_replay_evidence_review_next', False)).lower()}",
        f"  browser_replay_built: {str(payload.get('browser_replay_built', False)).lower()}",
        "  browser_execution_allowed: false",
        "  cdp_connection_allowed: false",
        "  authenticated_session_allowed: false",
        "  canonical_writeback_allowed: false",
    ]
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_browser_skill_shadow_replay_evidence_review_closeout(
    args: argparse.Namespace,
) -> int:
    """Review scoped shadow replay evidence provenance without browser execution."""
    try:
        payload = candidate_promotion_browser_skill_shadow_replay_evidence_review_closeout(
            args.candidate_id,
            _vault_root_arg(args),
            tenant_id=getattr(args, "tenant_id", None),
            workspace_id=getattr(args, "workspace_id", None),
            user_id=getattr(args, "user_id", None),
            actor=args.actor,
            target_url=args.target_url,
            shadow_mode=bool(getattr(args, "shadow_mode", False)),
            write_review_closeout=bool(getattr(args, "write_review_closeout", False)),
            local_target_only=bool(getattr(args, "local_target_only", False)),
            allowlisted_domain=getattr(args, "allowlisted_domain", None),
            max_steps=getattr(args, "max_steps", 5),
            source_approval_id=getattr(args, "source_approval_id", None),
            activation_approval_id=getattr(args, "activation_approval_id", None),
            reason=getattr(args, "reason", None),
        )
    except (SiteOpsError, BrowserSkillCandidateError, RuntimeError, ValueError) as exc:
        return _error(args, exc)
    lines = [
        "ChaseOS SiteOps Browser Skill Shadow Replay Evidence Review Closeout",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        "  browser_skill_shadow_replay_evidence_review_closeout_status: "
        f"{payload.get('browser_skill_shadow_replay_evidence_review_closeout_status')}",
        "  ready_for_local_shadow_execution_approval_next: "
        f"{str(payload.get('ready_for_local_shadow_execution_approval_next', False)).lower()}",
        "  write_review_closeout_requested: "
        f"{str(payload.get('write_review_closeout_requested', False)).lower()}",
        f"  review_closeout_written: {str(payload.get('review_closeout_written', False)).lower()}",
        f"  browser_run_ref: {payload.get('browser_run_ref')}",
        f"  review_closeout_ref: {payload.get('review_closeout_ref')}",
        "  trusted_promotion_allowed: false",
        "  browser_execution_allowed: false",
        "  cdp_connection_allowed: false",
        "  authenticated_session_allowed: false",
        "  canonical_writeback_allowed: false",
    ]
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_browser_skill_shadow_execution_approval_packet(
    args: argparse.Namespace,
) -> int:
    """Prepare a guarded local shadow execution approval packet without browser execution."""
    try:
        payload = candidate_promotion_browser_skill_shadow_execution_approval_packet(
            args.candidate_id,
            _vault_root_arg(args),
            tenant_id=getattr(args, "tenant_id", None),
            workspace_id=getattr(args, "workspace_id", None),
            user_id=getattr(args, "user_id", None),
            actor=args.actor,
            target_url=args.target_url,
            shadow_mode=bool(getattr(args, "shadow_mode", False)),
            write_approval_request=bool(getattr(args, "write_approval_request", False)),
            local_target_only=bool(getattr(args, "local_target_only", False)),
            allowlisted_domain=getattr(args, "allowlisted_domain", None),
            max_steps=getattr(args, "max_steps", 5),
            source_approval_id=getattr(args, "source_approval_id", None),
            activation_approval_id=getattr(args, "activation_approval_id", None),
            reason=getattr(args, "reason", None),
        )
    except (SiteOpsError, BrowserSkillCandidateError, RuntimeError, ValueError) as exc:
        return _error(args, exc)
    lines = [
        "ChaseOS SiteOps Browser Skill Shadow Execution Approval Packet",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        "  browser_skill_shadow_execution_approval_packet_status: "
        f"{payload.get('browser_skill_shadow_execution_approval_packet_status')}",
        "  approval_request_ready: "
        f"{str(payload.get('approval_request_ready', False)).lower()}",
        "  write_approval_request_requested: "
        f"{str(payload.get('write_approval_request_requested', False)).lower()}",
        f"  approval_request_written: {str(payload.get('approval_request_written', False)).lower()}",
        f"  approval_id: {payload.get('approval_id')}",
        f"  review_closeout_ref: {payload.get('review_closeout_ref')}",
        f"  future_browser_run_ref: {payload.get('future_browser_run_ref')}",
        "  ready_for_guarded_local_shadow_execution_proof_next: "
        f"{str(payload.get('ready_for_guarded_local_shadow_execution_proof_next', False)).lower()}",
        "  browser_execution_allowed: false",
        "  cdp_connection_allowed: false",
        "  authenticated_session_allowed: false",
        "  trusted_promotion_allowed: false",
        "  canonical_writeback_allowed: false",
    ]
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_browser_skill_shadow_execution_approval_decision_preflight(
    args: argparse.Namespace,
) -> int:
    """Validate a shadow execution approval request without deciding or consuming it."""
    try:
        payload = (
            candidate_promotion_browser_skill_shadow_execution_approval_decision_preflight(
                args.candidate_id,
                _vault_root_arg(args),
                tenant_id=getattr(args, "tenant_id", None),
                workspace_id=getattr(args, "workspace_id", None),
                user_id=getattr(args, "user_id", None),
                actor=args.actor,
                target_url=args.target_url,
                shadow_execution_approval_id=args.shadow_execution_approval_id,
                shadow_mode=bool(getattr(args, "shadow_mode", False)),
                local_target_only=bool(getattr(args, "local_target_only", False)),
                allowlisted_domain=getattr(args, "allowlisted_domain", None),
                max_steps=getattr(args, "max_steps", 5),
                source_approval_id=getattr(args, "source_approval_id", None),
                activation_approval_id=getattr(args, "activation_approval_id", None),
                reason=getattr(args, "reason", None),
            )
        )
    except (SiteOpsError, BrowserSkillCandidateError, RuntimeError, ValueError) as exc:
        return _error(args, exc)
    lines = [
        "ChaseOS SiteOps Browser Skill Shadow Execution Approval Decision Preflight",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        f"  shadow_execution_approval_id: {payload.get('shadow_execution_approval_id')}",
        "  shadow_execution_approval_decision_preflight_status: "
        f"{payload.get('shadow_execution_approval_decision_preflight_status')}",
        f"  approval_status: {payload.get('approval_status')}",
        "  browser_run_digest_matches: "
        f"{str(payload.get('browser_run_digest_matches', False)).lower()}",
        "  review_closeout_digest_matches: "
        f"{str(payload.get('review_closeout_digest_matches', False)).lower()}",
        "  future_write_set_matches: "
        f"{str(payload.get('future_write_set_matches', False)).lower()}",
        "  ready_for_shadow_execution_proof_review_next_pass: "
        f"{str(payload.get('ready_for_shadow_execution_proof_review_next_pass', False)).lower()}",
        "  approval_decision_written: false",
        "  approval_consumed: false",
        "  shadow_execution_proof_written: false",
        "  browser_execution_allowed: false",
        "  cdp_connection_allowed: false",
        "  authenticated_session_allowed: false",
        "  trusted_promotion_allowed: false",
        "  canonical_writeback_allowed: false",
    ]
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_browser_skill_shadow_execution_approval_decision_request(
    args: argparse.Namespace,
) -> int:
    """Approve/reject a shadow execution approval only behind an explicit write flag."""
    try:
        payload = (
            candidate_promotion_browser_skill_shadow_execution_approval_decision_request(
                args.candidate_id,
                _vault_root_arg(args),
                tenant_id=getattr(args, "tenant_id", None),
                workspace_id=getattr(args, "workspace_id", None),
                user_id=getattr(args, "user_id", None),
                actor=args.actor,
                target_url=args.target_url,
                shadow_execution_approval_id=args.shadow_execution_approval_id,
                decision=args.decision,
                shadow_mode=bool(getattr(args, "shadow_mode", False)),
                local_target_only=bool(getattr(args, "local_target_only", False)),
                allowlisted_domain=getattr(args, "allowlisted_domain", None),
                max_steps=getattr(args, "max_steps", 5),
                source_approval_id=getattr(args, "source_approval_id", None),
                activation_approval_id=getattr(args, "activation_approval_id", None),
                reason=getattr(args, "reason", None),
                write_approval_decision=bool(getattr(args, "write_approval_decision", False)),
            )
        )
    except (SiteOpsError, BrowserSkillCandidateError, RuntimeError, ValueError) as exc:
        return _error(args, exc)
    lines = [
        "ChaseOS SiteOps Browser Skill Shadow Execution Approval Decision Request",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        f"  shadow_execution_approval_id: {payload.get('shadow_execution_approval_id')}",
        f"  decision: {payload.get('decision')}",
        "  shadow_execution_approval_decision_request_status: "
        f"{payload.get('shadow_execution_approval_decision_request_status')}",
        f"  shadow_execution_proof_status: {payload.get('shadow_execution_proof_status')}",
        "  approval_decision_write_requested: "
        f"{str(payload.get('approval_decision_write_requested', False)).lower()}",
        f"  approval_decision_written: {str(payload.get('approval_decision_written', False)).lower()}",
        f"  approval_status_after_decision: {payload.get('approval_status_after_decision')}",
        "  approval_consumed: false",
        "  shadow_execution_proof_written: false",
        "  browser_execution_allowed: false",
        "  cdp_connection_allowed: false",
        "  authenticated_session_allowed: false",
        "  trusted_promotion_allowed: false",
        "  canonical_writeback_allowed: false",
    ]
    if payload.get("approval_ref"):
        lines.append(f"  approval_ref: {payload.get('approval_ref')}")
    if payload.get("audit_ref"):
        lines.append(f"  audit_ref: {payload.get('audit_ref')}")
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_browser_skill_shadow_execution_approval_live_decision_readiness(
    args: argparse.Namespace,
) -> int:
    """Report whether a live shadow execution approval decision is ready without writing."""
    try:
        payload = (
            candidate_promotion_browser_skill_shadow_execution_approval_live_decision_readiness(
                args.candidate_id,
                _vault_root_arg(args),
                tenant_id=getattr(args, "tenant_id", None),
                workspace_id=getattr(args, "workspace_id", None),
                user_id=getattr(args, "user_id", None),
                actor=args.actor,
                target_url=args.target_url,
                shadow_execution_approval_id=args.shadow_execution_approval_id,
                intended_decision=getattr(args, "intended_decision", None),
                shadow_mode=bool(getattr(args, "shadow_mode", False)),
                local_target_only=bool(getattr(args, "local_target_only", False)),
                allowlisted_domain=getattr(args, "allowlisted_domain", None),
                max_steps=getattr(args, "max_steps", 5),
                source_approval_id=getattr(args, "source_approval_id", None),
                activation_approval_id=getattr(args, "activation_approval_id", None),
                reason=getattr(args, "reason", None),
            )
        )
    except (SiteOpsError, BrowserSkillCandidateError, RuntimeError, ValueError) as exc:
        return _error(args, exc)
    lines = [
        "ChaseOS SiteOps Browser Skill Shadow Execution Approval Live Decision Readiness",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        f"  shadow_execution_approval_id: {payload.get('shadow_execution_approval_id')}",
        f"  intended_decision: {payload.get('intended_decision')}",
        "  shadow_execution_approval_live_decision_readiness_status: "
        f"{payload.get('shadow_execution_approval_live_decision_readiness_status')}",
        f"  approval_status: {payload.get('approval_status')}",
        "  explicit_operator_authorization_present: false",
        "  ready_for_live_decision_write_next_pass: "
        f"{str(payload.get('ready_for_live_decision_write_next_pass', False)).lower()}",
        "  live_decision_written: false",
        "  approval_decision_written: false",
        "  approval_consumed: false",
        "  shadow_execution_proof_written: false",
        "  browser_execution_allowed: false",
        "  cdp_connection_allowed: false",
        "  authenticated_session_allowed: false",
        "  trusted_promotion_allowed: false",
        "  canonical_writeback_allowed: false",
    ]
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_browser_skill_shadow_execution_proof_readiness(
    args: argparse.Namespace,
) -> int:
    """Report whether shadow execution proof is ready without launching a browser."""
    try:
        payload = candidate_promotion_browser_skill_shadow_execution_proof_readiness(
            args.candidate_id,
            _vault_root_arg(args),
            tenant_id=getattr(args, "tenant_id", None),
            workspace_id=getattr(args, "workspace_id", None),
            user_id=getattr(args, "user_id", None),
            actor=args.actor,
            target_url=args.target_url,
            shadow_execution_approval_id=args.shadow_execution_approval_id,
            shadow_mode=bool(getattr(args, "shadow_mode", False)),
            local_target_only=bool(getattr(args, "local_target_only", False)),
            allowlisted_domain=getattr(args, "allowlisted_domain", None),
            max_steps=getattr(args, "max_steps", 5),
            source_approval_id=getattr(args, "source_approval_id", None),
            activation_approval_id=getattr(args, "activation_approval_id", None),
            reason=getattr(args, "reason", None),
        )
    except (SiteOpsError, BrowserSkillCandidateError, RuntimeError, ValueError) as exc:
        return _error(args, exc)
    lines = [
        "ChaseOS SiteOps Browser Skill Shadow Execution Proof Readiness",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        f"  shadow_execution_approval_id: {payload.get('shadow_execution_approval_id')}",
        f"  approval_status: {payload.get('approval_status')}",
        f"  shadow_execution_proof_readiness_status: {payload.get('shadow_execution_proof_readiness_status')}",
        "  ready_for_shadow_execution_proof: "
        f"{str(payload.get('ready_for_shadow_execution_proof', False)).lower()}",
        "  approval_consumed: false",
        "  shadow_execution_proof_written: false",
        "  browser_execution_allowed: false",
        "  cdp_connection_allowed: false",
        "  authenticated_session_allowed: false",
        "  trusted_promotion_allowed: false",
        "  canonical_writeback_allowed: false",
    ]
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_browser_skill_shadow_execution_proof_consumption_guard(
    args: argparse.Namespace,
) -> int:
    """Guard shadow execution approval consumption without launching a browser."""
    try:
        payload = candidate_promotion_browser_skill_shadow_execution_proof_consumption_guard(
            args.candidate_id,
            _vault_root_arg(args),
            tenant_id=getattr(args, "tenant_id", None),
            workspace_id=getattr(args, "workspace_id", None),
            user_id=getattr(args, "user_id", None),
            actor=args.actor,
            target_url=args.target_url,
            shadow_execution_approval_id=args.shadow_execution_approval_id,
            shadow_mode=bool(getattr(args, "shadow_mode", False)),
            local_target_only=bool(getattr(args, "local_target_only", False)),
            allowlisted_domain=getattr(args, "allowlisted_domain", None),
            max_steps=getattr(args, "max_steps", 5),
            source_approval_id=getattr(args, "source_approval_id", None),
            activation_approval_id=getattr(args, "activation_approval_id", None),
            reason=getattr(args, "reason", None),
            consume_shadow_execution_approval=bool(
                getattr(args, "consume_shadow_execution_approval", False)
            ),
        )
    except (SiteOpsError, BrowserSkillCandidateError, RuntimeError, ValueError) as exc:
        return _error(args, exc)
    lines = [
        "ChaseOS SiteOps Browser Skill Shadow Execution Proof Consumption Guard",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        f"  shadow_execution_approval_id: {payload.get('shadow_execution_approval_id')}",
        "  shadow_execution_proof_consumption_guard_status: "
        f"{payload.get('shadow_execution_proof_consumption_guard_status')}",
        f"  approval_status: {payload.get('approval_status')}",
        "  consume_shadow_execution_approval_requested: "
        f"{str(payload.get('consume_shadow_execution_approval_requested', False)).lower()}",
        "  shadow_execution_consumer_ready_to_consume: "
        f"{str(payload.get('shadow_execution_consumer_ready_to_consume', False)).lower()}",
        "  shadow_execution_consumption_marker_written: "
        f"{str(payload.get('shadow_execution_consumption_marker_written', False)).lower()}",
        "  shadow_execution_consumer_audit_written: "
        f"{str(payload.get('shadow_execution_consumer_audit_written', False)).lower()}",
        f"  approval_consumed: {str(payload.get('approval_consumed', False)).lower()}",
        "  shadow_execution_proof_written: false",
        "  browser_execution_allowed: false",
        "  cdp_connection_allowed: false",
        "  authenticated_session_allowed: false",
        "  trusted_promotion_allowed: false",
        "  canonical_writeback_allowed: false",
    ]
    if payload.get("shadow_execution_consumer_marker_path"):
        lines.append(
            f"  shadow_execution_consumer_marker_path: {payload.get('shadow_execution_consumer_marker_path')}"
        )
    if payload.get("run_ref"):
        lines.append(f"  run_ref: {payload.get('run_ref')}")
    if payload.get("audit_ref"):
        lines.append(f"  audit_ref: {payload.get('audit_ref')}")
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_browser_skill_shadow_execution_proof(
    args: argparse.Namespace,
) -> int:
    """Write scoped shadow execution proof artifacts without launching a browser."""
    try:
        payload = candidate_promotion_browser_skill_shadow_execution_proof(
            args.candidate_id,
            _vault_root_arg(args),
            tenant_id=getattr(args, "tenant_id", None),
            workspace_id=getattr(args, "workspace_id", None),
            user_id=getattr(args, "user_id", None),
            actor=args.actor,
            target_url=args.target_url,
            shadow_execution_approval_id=args.shadow_execution_approval_id,
            shadow_mode=bool(getattr(args, "shadow_mode", False)),
            local_target_only=bool(getattr(args, "local_target_only", False)),
            allowlisted_domain=getattr(args, "allowlisted_domain", None),
            max_steps=getattr(args, "max_steps", 5),
            source_approval_id=getattr(args, "source_approval_id", None),
            activation_approval_id=getattr(args, "activation_approval_id", None),
            reason=getattr(args, "reason", None),
            write_shadow_execution_proof=bool(
                getattr(args, "write_shadow_execution_proof", False)
            ),
        )
    except (SiteOpsError, BrowserSkillCandidateError, RuntimeError, ValueError) as exc:
        return _error(args, exc)
    lines = [
        "ChaseOS SiteOps Browser Skill Shadow Execution Proof",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        f"  shadow_execution_approval_id: {payload.get('shadow_execution_approval_id')}",
        f"  shadow_execution_proof_status: {payload.get('shadow_execution_proof_status')}",
        "  write_shadow_execution_proof_requested: "
        f"{str(payload.get('write_shadow_execution_proof_requested', False)).lower()}",
        "  shadow_execution_proof_ready_to_write: "
        f"{str(payload.get('shadow_execution_proof_ready_to_write', False)).lower()}",
        f"  approval_consumed: {str(payload.get('approval_consumed', False)).lower()}",
        f"  shadow_execution_proof_written: {str(payload.get('shadow_execution_proof_written', False)).lower()}",
        "  browser_execution_allowed: false",
        "  cdp_connection_allowed: false",
        "  authenticated_session_allowed: false",
        "  trusted_promotion_allowed: false",
        "  canonical_writeback_allowed: false",
    ]
    if payload.get("browser_run_path"):
        lines.append(f"  browser_run_path: {payload.get('browser_run_path')}")
    if payload.get("agent_activity_path"):
        lines.append(f"  agent_activity_path: {payload.get('agent_activity_path')}")
    if payload.get("run_ref"):
        lines.append(f"  run_ref: {payload.get('run_ref')}")
    if payload.get("audit_ref"):
        lines.append(f"  audit_ref: {payload.get('audit_ref')}")
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_browser_skill_shadow_execution_proof_review_closeout(
    args: argparse.Namespace,
) -> int:
    """Review scoped shadow execution proof artifacts without launching a browser."""
    try:
        payload = candidate_promotion_browser_skill_shadow_execution_proof_review_closeout(
            args.candidate_id,
            _vault_root_arg(args),
            tenant_id=getattr(args, "tenant_id", None),
            workspace_id=getattr(args, "workspace_id", None),
            user_id=getattr(args, "user_id", None),
            actor=args.actor,
            target_url=args.target_url,
            shadow_execution_approval_id=args.shadow_execution_approval_id,
            shadow_mode=bool(getattr(args, "shadow_mode", False)),
            local_target_only=bool(getattr(args, "local_target_only", False)),
            allowlisted_domain=getattr(args, "allowlisted_domain", None),
            max_steps=getattr(args, "max_steps", 5),
            source_approval_id=getattr(args, "source_approval_id", None),
            activation_approval_id=getattr(args, "activation_approval_id", None),
            reason=getattr(args, "reason", None),
            write_review_closeout=bool(getattr(args, "write_review_closeout", False)),
        )
    except (SiteOpsError, BrowserSkillCandidateError, RuntimeError, ValueError) as exc:
        return _error(args, exc)
    lines = [
        "ChaseOS SiteOps Browser Skill Shadow Execution Proof Review Closeout",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        f"  shadow_execution_approval_id: {payload.get('shadow_execution_approval_id')}",
        "  shadow_execution_proof_review_closeout_status: "
        f"{payload.get('shadow_execution_proof_review_closeout_status')}",
        "  write_review_closeout_requested: "
        f"{str(payload.get('write_review_closeout_requested', False)).lower()}",
        "  review_closeout_written: "
        f"{str(payload.get('review_closeout_written', False)).lower()}",
        "  ready_for_trusted_promotion_review_next: "
        f"{str(payload.get('ready_for_trusted_promotion_review_next', False)).lower()}",
        "  trusted_promotion_allowed: false",
        "  browser_execution_allowed: false",
        "  cdp_connection_allowed: false",
        "  authenticated_session_allowed: false",
        "  canonical_writeback_allowed: false",
    ]
    if payload.get("review_closeout_path"):
        lines.append(f"  review_closeout_path: {payload.get('review_closeout_path')}")
    if payload.get("browser_run_ref"):
        lines.append(f"  browser_run_ref: {payload.get('browser_run_ref')}")
    if payload.get("proof_audit_ref"):
        lines.append(f"  proof_audit_ref: {payload.get('proof_audit_ref')}")
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_candidates_source_approval_rebind_live_readiness(args: argparse.Namespace) -> int:
    """Report whether a legacy source approval is ready for replacement without writing."""
    try:
        payload = candidate_promotion_source_approval_rebind_live_readiness(
            args.candidate_id,
            _vault_root_arg(args),
            tenant_id=getattr(args, "tenant_id", None),
            workspace_id=getattr(args, "workspace_id", None),
            user_id=getattr(args, "user_id", None),
            actor=args.actor,
            legacy_approval_id=getattr(args, "approval_id", None),
            reason=getattr(args, "reason", None),
        )
    except (SiteOpsError, BrowserSkillCandidateError, RuntimeError, ValueError) as exc:
        return _error(args, exc)
    lines = [
        "ChaseOS SiteOps Candidate Source Approval Rebind Live Readiness",
        f"  candidate_id: {payload.get('candidate_id')}",
        f"  proposed_skill_id: {payload.get('proposed_skill_id')}",
        f"  source_approval_id: {payload.get('source_approval_id')}",
        "  source_approval_rebind_live_readiness_status: "
        f"{payload.get('source_approval_rebind_live_readiness_status')}",
        f"  source_approval_status: {payload.get('source_approval_status')}",
        f"  source_approval_provenance_status: {payload.get('source_approval_provenance_status')}",
        "  replacement_approval_writer_dry_run_ready: "
        f"{str(payload.get('replacement_approval_writer_dry_run_ready', False)).lower()}",
        "  replacement_approval_request_written: false",
        "  approval_consumed: false",
        "  trusted_skill_write_allowed: false",
        "  activation_allowed: false",
        "  browser_execution_allowed: false",
        "  canonical_writeback_allowed: false",
    ]
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_catalog_list(args: argparse.Namespace) -> int:
    try:
        catalog = load_catalog(_vault_root_arg(args))
    except SiteOpsError as exc:
        return _error(args, exc)

    type_filter = getattr(args, "catalog_type", "all")
    mapping = {
        "skill": ("site_skill_templates", "skill_template_id"),
        "workflow": ("workflow_templates", "workflow_template_id"),
        "provider": ("provider_templates", "provider_adapter_id"),
        "policy": ("policy_packs", "policy_pack_id"),
    }
    selected = mapping if type_filter == "all" else {type_filter: mapping[type_filter]}
    items: list[dict[str, Any]] = []
    for item_type, (key, id_field) in selected.items():
        for item in catalog.get(key, []):
            items.append(
                {
                    "id": item.get(id_field),
                    "type": item_type,
                    "display_name": item.get("display_name"),
                    "status": item.get("status"),
                    "version": item.get("version"),
                    "risk_level": item.get("risk_level"),
                    "visibility": item.get("visibility"),
                }
            )
    payload = {"ok": True, "catalog_type": type_filter, "count": len(items), "items": items}
    lines = ["ChaseOS SiteOps Catalog", f"  catalog_type: {type_filter}", f"  count: {len(items)}"]
    for item in items:
        lines.append(f"  - {item['type']}: {item['id']} ({item.get('status')})")
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_catalog_show(args: argparse.Namespace) -> int:
    try:
        catalog = load_catalog(_vault_root_arg(args))
    except SiteOpsError as exc:
        return _error(args, exc)

    object_id = args.object_id
    mapping = {
        "skill": ("site_skill_templates", "skill_template_id"),
        "workflow": ("workflow_templates", "workflow_template_id"),
        "provider": ("provider_templates", "provider_adapter_id"),
        "policy": ("policy_packs", "policy_pack_id"),
    }
    type_filter = getattr(args, "catalog_type", None)
    selected = {type_filter: mapping[type_filter]} if type_filter else mapping
    for item_type, (key, id_field) in selected.items():
        item = objects_by_id(catalog.get(key, []), id_field).get(object_id)
        if item:
            payload = {"ok": True, "object_type": item_type, "object": item}
            lines = ["ChaseOS SiteOps Catalog Object", f"  id: {object_id}", f"  type: {item_type}", f"  status: {item.get('status')}"]
            return _print_json_or_text(args, payload, lines)
    return _error(args, SiteOpsRegistryError(f"SiteOps catalog object not found: {object_id}"))


def cmd_siteops_tenants_list(args: argparse.Namespace) -> int:
    try:
        tenants = list_tenants(_vault_root_arg(args))
    except SiteOpsError as exc:
        return _error(args, exc)
    payload = {"ok": True, "count": len(tenants), "tenants": tenants}
    lines = ["ChaseOS SiteOps Tenants", f"  count: {len(tenants)}"]
    for tenant in tenants:
        lines.append(f"  - {tenant.get('tenant_id')}: {tenant.get('display_name')} ({tenant.get('status')})")
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_skills_list(args: argparse.Namespace) -> int:
    try:
        tenant = load_tenant(_vault_root_arg(args), _tenant_arg(args))
    except SiteOpsError as exc:
        return _error(args, exc)
    items = list(tenant.get("site_skill_installations", []))
    payload = {"ok": True, "tenant_id": _tenant_arg(args), "count": len(items), "skills": items}
    lines = ["ChaseOS SiteOps Skills", f"  tenant_id: {_tenant_arg(args)}", f"  count: {len(items)}"]
    for item in items:
        lines.append(f"  - {item.get('installation_id')}: {item.get('skill_template_id')} enabled={item.get('enabled')}")
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_skills_install(args: argparse.Namespace) -> int:
    try:
        root = _vault_root_arg(args)
        tenant_id = _tenant_arg(args)
        actor = getattr(args, "actor", None) or DEFAULT_LOCAL_SCOPE["user_id"]
        catalog = load_catalog(root)
        tenant = load_tenant(root, tenant_id)
        templates = objects_by_id(catalog.get("site_skill_templates", []), "skill_template_id")
        template = templates.get(args.skill_template_id)
        if not template:
            raise SiteOpsRegistryError(f"SiteSkillTemplate not found: {args.skill_template_id}")
        existing = next(
            (
                item
                for item in tenant.get("site_skill_installations", [])
                if item.get("skill_template_id") == args.skill_template_id
            ),
            None,
        )
        if existing:
            payload = {"ok": True, "status": "already_installed", "installation": existing}
        else:
            meta = tenant.get("tenant", {})
            installation = {
                "installation_id": f"{tenant_id}-{_slug(args.skill_template_id)}",
                "tenant_id": tenant_id,
                "skill_template_id": args.skill_template_id,
                "enabled": True,
                "allowed_workspaces": [meta.get("default_workspace_id", DEFAULT_LOCAL_SCOPE["workspace_id"])],
                "allowed_roles": ["workflow_runner", "workflow_author", "workspace_admin", "tenant_admin"],
                "policy_overrides": {},
                "provider_overrides": {},
                "approval_overrides": {},
                "budget_policy_id": None,
                "default_policy_pack": template.get("default_policy_pack", "siteops_default_v1"),
                "risk_level": template.get("risk_level", "medium"),
                "created_by": actor,
                "updated_by": actor,
                "owner_type": "tenant",
                "visibility": "tenant",
                "version": "0.1.0",
                "status": "CONFIGURED BUT UNVERIFIED",
            }
            tenant.setdefault("site_skill_installations", []).append(installation)
            tenant_ref = save_tenant(root, tenant_id, tenant)
            payload = {"ok": True, "status": "installed", "installation": installation, "tenant_ref": str(tenant_ref)}
    except (SiteOpsError, SiteOpsRegistryError) as exc:
        return _error(args, exc)
    lines = ["ChaseOS SiteOps Skill Install", f"  status: {payload['status']}", f"  installation_id: {payload['installation'].get('installation_id')}"]
    return _print_json_or_text(args, payload, lines)


def _set_skill_enabled(args: argparse.Namespace, enabled: bool) -> int:
    try:
        root = _vault_root_arg(args)
        tenant_id = _tenant_arg(args)
        tenant = load_tenant(root, tenant_id)
        target = None
        for item in tenant.get("site_skill_installations", []):
            if item.get("installation_id") == args.installation_id:
                target = item
                break
        if not target:
            raise SiteOpsRegistryError(f"TenantSiteSkillInstallation not found: {args.installation_id}")
        target["enabled"] = enabled
        target["updated_by"] = getattr(args, "actor", None) or DEFAULT_LOCAL_SCOPE["user_id"]
        target["updated_at"] = datetime.now(timezone.utc).isoformat()
        tenant_ref = save_tenant(root, tenant_id, tenant)
        payload = {"ok": True, "installation": target, "tenant_ref": str(tenant_ref)}
    except (SiteOpsError, SiteOpsRegistryError) as exc:
        return _error(args, exc)
    lines = ["ChaseOS SiteOps Skill Status", f"  installation_id: {args.installation_id}", f"  enabled: {enabled}"]
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_skills_enable(args: argparse.Namespace) -> int:
    return _set_skill_enabled(args, True)


def cmd_siteops_skills_disable(args: argparse.Namespace) -> int:
    return _set_skill_enabled(args, False)


def _workflow_detail(root: str | None, tenant_id: str, workflow_id: str) -> dict[str, Any]:
    catalog = load_catalog(root)
    tenant = load_tenant(root, tenant_id)
    installs = tenant.get("workflow_installations", [])
    install = next(
        (
            item
            for item in installs
            if item.get("workflow_installation_id") == workflow_id or item.get("workflow_template_id") == workflow_id
        ),
        None,
    )
    templates = objects_by_id(catalog.get("workflow_templates", []), "workflow_template_id")
    template = templates.get(workflow_id) or (templates.get(install.get("workflow_template_id")) if install else None)
    if not install and not template:
        raise SiteOpsRegistryError(f"Workflow not found: {workflow_id}")
    return {"workflow_installation": install, "workflow_template": template}


def cmd_siteops_workflows_list(args: argparse.Namespace) -> int:
    try:
        tenant_id = _tenant_arg(args)
        workspace_id = getattr(args, "workspace_id", None)
        tenant = load_tenant(_vault_root_arg(args), tenant_id)
        workflows = [
            item
            for item in tenant.get("workflow_installations", [])
            if not workspace_id or item.get("workspace_id") in (None, workspace_id)
        ]
        payload = {"ok": True, "tenant_id": tenant_id, "workspace_id": workspace_id, "count": len(workflows), "workflows": workflows}
    except SiteOpsError as exc:
        return _error(args, exc)
    lines = ["ChaseOS SiteOps Workflows", f"  tenant_id: {tenant_id}", f"  count: {len(workflows)}"]
    for item in workflows:
        lines.append(f"  - {item.get('workflow_installation_id')}: {item.get('workflow_template_id')} enabled={item.get('enabled')}")
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_workflows_show(args: argparse.Namespace) -> int:
    try:
        payload = {"ok": True, "tenant_id": _tenant_arg(args), **_workflow_detail(_vault_root_arg(args), _tenant_arg(args), args.workflow_id)}
    except (SiteOpsError, SiteOpsRegistryError) as exc:
        return _error(args, exc)
    lines = ["ChaseOS SiteOps Workflow", f"  workflow_id: {args.workflow_id}", f"  tenant_id: {_tenant_arg(args)}"]
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_workflows_validate(args: argparse.Namespace) -> int:
    try:
        detail = _workflow_detail(_vault_root_arg(args), _tenant_arg(args), args.workflow_id)
        validation = validate_production_siteops(_vault_root_arg(args), _tenant_arg(args))
        payload = {"ok": validation["ok"], "tenant_id": _tenant_arg(args), "workflow_id": args.workflow_id, "validation": validation, **detail}
    except (SiteOpsError, SiteOpsRegistryError) as exc:
        return _error(args, exc)
    lines = [
        "ChaseOS SiteOps Workflow Validation",
        f"  ok: {payload['ok']}",
        f"  tenant_id: {_tenant_arg(args)}",
        f"  workflow_id: {args.workflow_id}",
        f"  errors: {len(payload['validation'].get('errors', []))}",
    ]
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_workflows_dry_run(args: argparse.Namespace) -> int:
    try:
        inputs = parse_cli_inputs(getattr(args, "inputs", None))
        payload = run_siteops_dry_run(
            root=_vault_root_arg(args),
            workflow_id=args.workflow_id,
            tenant_id=getattr(args, "tenant_id", None),
            workspace_id=getattr(args, "workspace_id", None),
            user_id=getattr(args, "user_id", None),
            inputs=inputs,
            action=getattr(args, "action", None),
            write_artifacts=True,
        )
    except (SiteOpsError, SiteOpsRegistryError) as exc:
        return _error(args, exc)
    lines = [
        "ChaseOS SiteOps Production Dry Run",
        f"  workflow_id: {args.workflow_id}",
        f"  run_id: {payload['run']['run_id']}",
        f"  status: {payload['run']['status']}",
    ] + _scope_lines(payload)
    if payload.get("approval"):
        lines.append(f"  approval_id: {payload['approval'].get('approval_id')}")
    lines.append(f"  run_ref: {payload.get('run_ref')}")
    lines.append(f"  audit_ref: {payload.get('audit_ref')}")
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_runs_list(args: argparse.Namespace) -> int:
    try:
        runs = list_run_records(_vault_root_arg(args), tenant_id=_tenant_arg(args), workspace_id=getattr(args, "workspace_id", None))
    except SiteOpsError as exc:
        return _error(args, exc)
    payload = {"ok": True, "tenant_id": _tenant_arg(args), "workspace_id": getattr(args, "workspace_id", None), "count": len(runs), "runs": runs}
    lines = ["ChaseOS SiteOps Runs", f"  tenant_id: {_tenant_arg(args)}", f"  count: {len(runs)}"]
    for run in runs:
        lines.append(f"  - {run.get('run_id')}: {run.get('workflow_id')} ({run.get('status')})")
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_runs_show(args: argparse.Namespace) -> int:
    try:
        run = show_run_record(_vault_root_arg(args), args.run_id, tenant_id=getattr(args, "tenant_id", None))
    except Exception as exc:
        return _error(args, exc)
    payload = {"ok": True, "run": run}
    lines = ["ChaseOS SiteOps Run", f"  run_id: {args.run_id}", f"  status: {run.get('status')}", f"  tenant_id: {run.get('tenant_id')}"]
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_runs_dry_run(args: argparse.Namespace) -> int:
    return cmd_siteops_workflows_dry_run(args)


def cmd_siteops_approvals_list(args: argparse.Namespace) -> int:
    try:
        approvals = list_approval_requests(_vault_root_arg(args), tenant_id=_tenant_arg(args), workspace_id=getattr(args, "workspace_id", None))
    except SiteOpsError as exc:
        return _error(args, exc)
    payload = {"ok": True, "tenant_id": _tenant_arg(args), "workspace_id": getattr(args, "workspace_id", None), "count": len(approvals), "approvals": approvals}
    lines = ["ChaseOS SiteOps Approvals", f"  tenant_id: {_tenant_arg(args)}", f"  count: {len(approvals)}"]
    for item in approvals:
        lines.append(f"  - {item.get('approval_id')}: {item.get('status')} action={item.get('action')}")
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_approvals_show(args: argparse.Namespace) -> int:
    try:
        approval = show_approval_request(_vault_root_arg(args), args.approval_id, tenant_id=getattr(args, "tenant_id", None))
    except SiteOpsError as exc:
        return _error(args, exc)
    payload = {"ok": True, "approval": approval}
    lines = ["ChaseOS SiteOps Approval", f"  approval_id: {args.approval_id}", f"  status: {approval.get('status')}"]
    return _print_json_or_text(args, payload, lines)


def _decide_approval(args: argparse.Namespace, status: str) -> int:
    try:
        approval = decide_approval_request(
            _vault_root_arg(args),
            args.approval_id,
            actor=args.actor,
            status=status,
            tenant_id=getattr(args, "tenant_id", None),
        )
    except SiteOpsError as exc:
        return _error(args, exc)
    payload = {"ok": True, "approval": approval}
    lines = ["ChaseOS SiteOps Approval Decision", f"  approval_id: {args.approval_id}", f"  status: {approval.get('status')}", f"  decided_by: {approval.get('decided_by')}"]
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_approvals_approve(args: argparse.Namespace) -> int:
    return _decide_approval(args, "approved")


def cmd_siteops_approvals_reject(args: argparse.Namespace) -> int:
    return _decide_approval(args, "rejected")


def cmd_siteops_credentials_list(args: argparse.Namespace) -> int:
    try:
        credentials = list_credential_refs(_vault_root_arg(args), tenant_id=_tenant_arg(args))
    except SiteOpsError as exc:
        return _error(args, exc)
    payload = {"ok": True, "tenant_id": _tenant_arg(args), "count": len(credentials), "credentials": credentials}
    lines = ["ChaseOS SiteOps Credential Refs", f"  tenant_id: {_tenant_arg(args)}", f"  count: {len(credentials)}"]
    for item in credentials:
        lines.append(f"  - {item.get('credential_ref_id')}: {item.get('provider_id')} ({item.get('status')})")
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_credentials_check(args: argparse.Namespace) -> int:
    try:
        credential = check_credential_ref(
            _vault_root_arg(args),
            credential_ref_id=args.credential_ref_id,
            tenant_id=_tenant_arg(args),
            user_id=getattr(args, "user_id", None),
        )
    except SiteOpsError as exc:
        return _error(args, exc)
    payload = {"ok": True, "credential": credential}
    lines = ["ChaseOS SiteOps Credential Check", f"  credential_ref_id: {args.credential_ref_id}", f"  configured: {credential.get('configured')}", "  secret_value_visible: False"]
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_browser_profiles_list(args: argparse.Namespace) -> int:
    try:
        profiles = list_browser_profile_refs(_vault_root_arg(args), tenant_id=_tenant_arg(args), user_id=getattr(args, "user_id", None))
    except SiteOpsError as exc:
        return _error(args, exc)
    payload = {"ok": True, "tenant_id": _tenant_arg(args), "user_id": getattr(args, "user_id", None), "count": len(profiles), "browser_profiles": profiles}
    lines = ["ChaseOS SiteOps Browser Profiles", f"  tenant_id: {_tenant_arg(args)}", f"  count: {len(profiles)}"]
    for item in profiles:
        lines.append(f"  - {item.get('browser_profile_ref_id')}: {item.get('provider')} ({item.get('status')})")
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_browser_profiles_check(args: argparse.Namespace) -> int:
    try:
        profile = check_browser_profile_ref(
            _vault_root_arg(args),
            browser_profile_ref_id=args.browser_profile_ref_id,
            tenant_id=_tenant_arg(args),
            user_id=getattr(args, "user_id", None),
        )
    except SiteOpsError as exc:
        return _error(args, exc)
    payload = {"ok": True, "browser_profile": profile}
    lines = ["ChaseOS SiteOps Browser Profile Check", f"  browser_profile_ref_id: {args.browser_profile_ref_id}", f"  configured: {profile.get('configured')}", "  session_value_visible: False"]
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_budgets_list(args: argparse.Namespace) -> int:
    try:
        budgets = list_budget_policies(_vault_root_arg(args), tenant_id=_tenant_arg(args))
    except SiteOpsError as exc:
        return _error(args, exc)
    payload = {"ok": True, "tenant_id": _tenant_arg(args), "count": len(budgets), "budgets": budgets}
    lines = ["ChaseOS SiteOps Budgets", f"  tenant_id: {_tenant_arg(args)}", f"  count: {len(budgets)}"]
    for item in budgets:
        lines.append(f"  - {item.get('budget_policy_id')}: {item.get('provider_id')} ({item.get('status')})")
    return _print_json_or_text(args, payload, lines)


def cmd_siteops_budgets_check(args: argparse.Namespace) -> int:
    try:
        budget = check_budget_policy(
            _vault_root_arg(args),
            tenant_id=_tenant_arg(args),
            provider_id=args.provider_id,
            estimated_cost=getattr(args, "estimated_cost", "0"),
        )
    except SiteOpsError as exc:
        return _error(args, exc)
    payload = {"ok": True, "budget": budget}
    lines = ["ChaseOS SiteOps Budget Check", f"  provider_id: {args.provider_id}", f"  decision: {budget.get('decision')}", f"  charged: {budget.get('charged')}"]
    return _print_json_or_text(args, payload, lines)
