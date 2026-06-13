"""Studio MVP deferral closeout audit.

This read-only audit turns the current Studio MVP tail into an operator-facing
decision matrix. It is intentionally not an executor: it does not create
credentials, read secrets, consume approvals, sign artifacts, launch apps, call
providers, control browsers, mutate targets, write Agent Bus tasks, or update
canonical state.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any

from runtime.studio.pass10b_expansion_pack_completion_audit import (
    DEFAULT_APPROVAL_PACKET_ID,
    build_pass10b_expansion_pack_completion_audit,
)


MODEL_VERSION = "studio.mvp_deferral_closeout_audit.v1"
SURFACE_ID = "studio_mvp_deferral_closeout_audit"
PASS_ID = "studio-mvp-deferral-closeout-audit"
STATUS = "PARTIAL / OPERATOR DECISION REQUIRED / MVP NOT CLOSED"
NEXT_RECOMMENDED_PASS = "operator-select-mvp-deferrals-or-governed-execution"
DEFAULT_REPORT_ROOT = Path("07_LOGS") / "Studio-Graph-Views" / "studio-mvp-deferral-closeout-audits"


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _safe_slug(value: str | None) -> str:
    raw = value or datetime.now(timezone.utc).strftime("%Y-%m-%d-studio-mvp-deferral-closeout-audit")
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", raw.strip()).strip(".-")
    return slug or "studio-mvp-deferral-closeout-audit"


def _relative_to_vault(vault: Path, path: str | Path | None) -> str | None:
    if path is None:
        return None
    resolved = Path(path)
    if not resolved.is_absolute():
        resolved = vault / resolved
    try:
        return resolved.resolve().relative_to(vault.resolve()).as_posix()
    except ValueError:
        return str(resolved)


def _resolve_report_root(vault: Path, report_root: str | Path | None) -> Path:
    root_input = Path(report_root) if report_root else DEFAULT_REPORT_ROOT
    root = root_input if root_input.is_absolute() else vault / root_input
    root = root.resolve()
    try:
        root.relative_to(vault.resolve())
    except ValueError as exc:
        raise ValueError("Studio MVP deferral closeout report root must stay inside the vault workspace") from exc
    return root


def _authority() -> dict[str, Any]:
    return {
        "read_only": True,
        "closeout_audit_only": True,
        "report_write_allowed_when_requested": True,
        "implementation_authority_granted": False,
        "approval_queue_write_allowed": False,
        "approval_consumption_allowed": False,
        "approval_execution_allowed": False,
        "signing_allowed": False,
        "reads_signing_certificate": False,
        "reads_credentials_or_secrets": False,
        "provider_calls_allowed": False,
        "model_calls_allowed": False,
        "runtime_dispatch_allowed": False,
        "browser_control_allowed": False,
        "browser_launch_allowed": False,
        "app_launch_allowed": False,
        "host_mutation_allowed": False,
        "registry_write_allowed": False,
        "startup_mutation_allowed": False,
        "release_promotion_allowed": False,
        "target_mutation_allowed": False,
        "agent_bus_task_write_allowed": False,
        "canonical_mutation_allowed": False,
    }


def _operator_item(
    item_id: str,
    title: str,
    *,
    status: str,
    current_truth: str,
    operator_required: bool,
    operator_input_types: list[str],
    operator_action: str,
    human_in_loop_reason: str,
    automation_allowed_now: bool,
    can_defer: bool,
    deferral_requirement: str,
    next_governed_surface: str | None,
    evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "id": item_id,
        "title": title,
        "status": status,
        "current_truth": current_truth,
        "operator_required": operator_required,
        "operator_input_types": operator_input_types,
        "operator_action": operator_action,
        "human_in_loop_reason": human_in_loop_reason,
        "automation_allowed_now": automation_allowed_now,
        "can_defer": can_defer,
        "deferral_requirement": deferral_requirement,
        "next_governed_surface": next_governed_surface,
        "evidence": evidence or {},
    }


def _installer_zip_proof_complete(pass10b: dict[str, Any]) -> bool:
    summary = pass10b.get("summary") or {}
    return bool(
        summary.get("approved_execution_performed") is True
        and summary.get("installer_outputs_present") is True
        and summary.get("current_pass10b_visual_proof_verified") is True
        and summary.get("no_forbidden_mutation_detected") is True
    )


def _mvp_items(pass10b: dict[str, Any]) -> list[dict[str, Any]]:
    pass10b_summary = pass10b.get("summary") or {}
    installer_complete = _installer_zip_proof_complete(pass10b)
    installer_status = "COMPLETE / VERIFIED" if installer_complete else "PARTIAL / EVIDENCE GAP"
    installer_truth = (
        "Pass 10B zip-portable installer build proof has approved execution evidence."
        if installer_complete
        else "Pass 10B installer build proof is not complete in the current evidence set."
    )
    installer_evidence = {
        "approval_packet_id": pass10b_summary.get("approval_packet_id") or DEFAULT_APPROVAL_PACKET_ID,
        "current_pass10b_visual_proof_verified": pass10b_summary.get("current_pass10b_visual_proof_verified"),
        "approved_execution_performed": pass10b_summary.get("approved_execution_performed"),
        "installer_outputs_present": pass10b_summary.get("installer_outputs_present"),
        "no_forbidden_mutation_detected": pass10b_summary.get("no_forbidden_mutation_detected"),
        "full_pass10b_expansion_pack_complete": pass10b.get("complete"),
        "next_recommended_pass": pass10b.get("next_recommended_pass"),
    }

    return [
        _operator_item(
            "pass10b_installer_zip_proof",
            "Pass 10B Installer ZIP Proof",
            status=installer_status,
            current_truth=installer_truth,
            operator_required=False,
            operator_input_types=[],
            operator_action="No operator input required for this already-audited ZIP proof unless you want a fresh rerun.",
            human_in_loop_reason="Existing evidence is sufficient for the ZIP proof lane.",
            automation_allowed_now=False,
            can_defer=False,
            deferral_requirement="Not a deferral candidate; this is already the completed baseline evidence.",
            next_governed_surface="pass10b-expansion-pack-completion-audit",
            evidence=installer_evidence,
        ),
        _operator_item(
            "branded_installer_logo_icon",
            "Branded Installer Logo/Icon Packaging",
            status="PLANNED / OPERATOR BRAND DECISION REQUIRED",
            current_truth="Repo truth says the current package is ZIP-portable and does not include final branded installer logo/icon packaging.",
            operator_required=True,
            operator_input_types=["brand_asset_or_design_decision", "manual_visual_review", "approval"],
            operator_action="Provide the canonical logo/icon assets or approve generated/selected assets, then approve a packaging rebuild.",
            human_in_loop_reason="Brand assets and visual acceptance are product decisions; Codex should not invent canonical branding and mark it final.",
            automation_allowed_now=False,
            can_defer=True,
            deferral_requirement="Operator must explicitly accept an unbranded/placeholder ZIP MVP or create a follow-up branded packaging lane.",
            next_governed_surface="installer-plan",
        ),
        _operator_item(
            "signing_chain",
            "Code Signing Chain",
            status="BLOCKED / CREDENTIALS AND APPROVAL REQUIRED",
            current_truth="Signing surfaces exist, but real signing cannot be completed without operator-supplied certificate material and an explicit signing approval.",
            operator_required=True,
            operator_input_types=["credential_or_secret", "environment_variable", "approval", "manual_verification"],
            operator_action=(
                "Choose the signing profile, provide certificate path/thumbprint and password/token through the approved secret mechanism, "
                "then approve the signing review/consumption/execution sequence."
            ),
            human_in_loop_reason="Signing requires private credentials and release authority that must remain outside autonomous Codex control.",
            automation_allowed_now=False,
            can_defer=True,
            deferral_requirement="Operator must explicitly accept unsigned artifacts for MVP or keep signing as a release-blocking follow-up.",
            next_governed_surface="signing-approval-preview",
        ),
        _operator_item(
            "startup_autostart_host_mutation",
            "Startup/Autostart Host Mutation",
            status="BLOCKED / HOST MUTATION APPROVAL REQUIRED",
            current_truth="Startup/autostart approval surfaces exist, but no autonomous host mutation is permitted by the current audit boundary.",
            operator_required=True,
            operator_input_types=["host_admin_action", "approval", "manual_test"],
            operator_action="Approve the exact startup/autostart target and manually verify rollback/disable behavior after any execution.",
            human_in_loop_reason="Autostart changes mutate the operator host and may require OS-level trust, admin context, and rollback judgment.",
            automation_allowed_now=False,
            can_defer=True,
            deferral_requirement="Operator must explicitly declare startup/autostart out of MVP scope or approve the governed host-mutation lane.",
            next_governed_surface="startup-autostart-approval-preview",
        ),
        _operator_item(
            "release_promotion",
            "Release Promotion",
            status="BLOCKED / RELEASE DECISION REQUIRED",
            current_truth="Release promotion surfaces exist, but current repo truth does not show final release promotion as complete.",
            operator_required=True,
            operator_input_types=["operator_decision", "approval", "manual_review"],
            operator_action="Choose release channel/version/tag, approve promotion criteria, and confirm whether unsigned or unbranded assets are acceptable.",
            human_in_loop_reason="Release promotion changes product status and distribution truth; it requires operator acceptance of known deferrals.",
            automation_allowed_now=False,
            can_defer=True,
            deferral_requirement="Operator must explicitly keep the MVP internal/unpromoted or approve the governed release-promotion lane.",
            next_governed_surface="release-promotion-approval-preview",
        ),
        _operator_item(
            "real_install_launch_manual_test",
            "Real Install/Launch Manual Test",
            status="BLOCKED / OPERATOR MANUAL TEST REQUIRED",
            current_truth="Automated package evidence exists, but current closeout still needs a real operator acceptance test or explicit deferral.",
            operator_required=True,
            operator_input_types=["manual_test", "approval"],
            operator_action="Run or approve a real install/launch test on the target host and confirm observed behavior, screenshots, and rollback result.",
            human_in_loop_reason="MVP acceptance depends on the actual operator environment, OS policy, WebView runtime, and human-observed launch quality.",
            automation_allowed_now=False,
            can_defer=True,
            deferral_requirement="Operator must explicitly accept automated packaging evidence as enough for this MVP slice or request manual test execution.",
            next_governed_surface="packaged-app-launch-smoke",
        ),
        _operator_item(
            "real_target_workspace_migration",
            "Real Target Workspace Migration",
            status="BLOCKED / TARGET PATH AND APPROVAL REQUIRED",
            current_truth="Upgrade proof surfaces are bounded/temp-target; real target workspace mutation remains unexecuted unless you choose and approve a target.",
            operator_required=True,
            operator_input_types=["operator_selected_path", "approval", "manual_backup_confirmation", "manual_test"],
            operator_action="Provide the exact target workspace path, confirm backup expectations, approve mutation, and verify the upgraded workspace.",
            human_in_loop_reason="A real workspace migration mutates user-selected data and must not be inferred from repo context.",
            automation_allowed_now=False,
            can_defer=True,
            deferral_requirement="Operator must explicitly defer real target migration or approve the governed target-upgrade executor.",
            next_governed_surface="approved-target-upgrade-executor",
        ),
        _operator_item(
            "provider_model_live_calls",
            "Provider/Model Live Calls",
            status="BLOCKED / ENV AND PROVIDER APPROVAL REQUIRED",
            current_truth="Live provider/model execution remains governed and unverified for Studio closeout.",
            operator_required=True,
            operator_input_types=["environment_variable", "credential_or_secret", "provider_budget_decision", "approval"],
            operator_action="Provide provider credentials/env, choose provider/model/budget, and approve any live call or smoke probe.",
            human_in_loop_reason="Live calls may spend money, expose data to external providers, or depend on private keys.",
            automation_allowed_now=False,
            can_defer=True,
            deferral_requirement="Operator must explicitly keep live provider calls outside MVP or approve a governed live-provider proof.",
            next_governed_surface="phase11-chat-live-provider-execution-approval-preview",
        ),
        _operator_item(
            "runtime_dispatch_activation",
            "Runtime/Adapter Dispatch Activation",
            status="BLOCKED / RUNTIME AUTHORITY REQUIRED",
            current_truth="Runtime dispatch/readiness surfaces exist, but actual runtime/adapter activation is not proven as completed for the MVP closeout.",
            operator_required=True,
            operator_input_types=["operator_decision", "approval", "runtime_target_selection", "manual_monitoring"],
            operator_action="Select the runtime/adapter target, approve dispatch authority, and monitor the first live run/rollback path.",
            human_in_loop_reason="Dispatch activates bounded runtimes and may write runtime artifacts or trigger external work.",
            automation_allowed_now=False,
            can_defer=True,
            deferral_requirement="Operator must explicitly keep runtime dispatch disabled for MVP or approve a governed dispatch executor.",
            next_governed_surface="phase11-chat-runtime-dispatch-readiness-contract",
        ),
        _operator_item(
            "browser_dispatch_activation",
            "Browser Dispatch Activation",
            status="BLOCKED / TARGET URL OR PROFILE AND APPROVAL REQUIRED",
            current_truth="Browser dispatch remains governed; current repo truth does not show real browser control as completed for closeout.",
            operator_required=True,
            operator_input_types=["external_target", "browser_profile_decision", "approval", "manual_test"],
            operator_action="Provide/approve the target URL or local target, choose profile/session boundaries, then approve browser control and verify output.",
            human_in_loop_reason="Browser control can expose sessions, cookies, credentials, or external targets and must remain operator-selected.",
            automation_allowed_now=False,
            can_defer=True,
            deferral_requirement="Operator must explicitly keep browser dispatch out of MVP or approve a governed browser-dispatch proof.",
            next_governed_surface="phase11-chat-browser-dispatch-readiness-contract",
        ),
        _operator_item(
            "companion_selection_executor",
            "Companion Selection Approval Consumption Executor",
            status="BLOCKED / APPROVAL CONSUMPTION REQUIRED",
            current_truth="Companion selection previews/readiness exist, but the consuming executor remains outside no-HITL authority.",
            operator_required=True,
            operator_input_types=["operator_decision", "approval", "target_state_review"],
            operator_action="Approve the specific companion-selection artifact and permit the executor to consume it against the selected target.",
            human_in_loop_reason="Consumption changes target selection state and must be explicitly tied to a chosen artifact.",
            automation_allowed_now=False,
            can_defer=True,
            deferral_requirement="Operator must explicitly defer selection consumption or approve the governed companion-selection execution lane.",
            next_governed_surface="phase11-chat-companion-selection-approval-consumption-readiness",
        ),
        _operator_item(
            "persisted_graph_storage_durable_ids",
            "Persisted Graph Storage/Durable IDs",
            status="PLANNED / PRODUCT SCOPE DECISION REQUIRED",
            current_truth="Graph view and index surfaces exist, but durable persisted graph storage remains a product/architecture follow-up unless explicitly scoped in.",
            operator_required=True,
            operator_input_types=["operator_decision", "architecture_scope_decision", "manual_acceptance"],
            operator_action="Decide whether durable graph storage is required for MVP closeout or record it as a post-MVP architecture lane.",
            human_in_loop_reason="This is a scope boundary decision, not a credential issue; MVP status depends on whether the operator includes it.",
            automation_allowed_now=False,
            can_defer=True,
            deferral_requirement="Operator must explicitly accept current read-only/derived graph surfaces as sufficient or authorize implementation.",
            next_governed_surface="graph-index-contract",
        ),
    ]


def _operator_summary(items: list[dict[str, Any]]) -> dict[str, Any]:
    required_items = [item for item in items if item["operator_required"]]
    deferrable_required = [item for item in required_items if item["can_defer"]]
    type_counts: dict[str, int] = {}
    for item in required_items:
        for input_type in item.get("operator_input_types") or []:
            type_counts[input_type] = type_counts.get(input_type, 0) + 1
    return {
        "operator_required_item_count": len(required_items),
        "operator_not_required_item_count": len(items) - len(required_items),
        "operator_input_type_counts": dict(sorted(type_counts.items())),
        "deferrable_operator_item_count": len(deferrable_required),
        "credential_or_secret_required": any(
            "credential_or_secret" in (item.get("operator_input_types") or []) for item in required_items
        ),
        "environment_variable_required": any(
            "environment_variable" in (item.get("operator_input_types") or []) for item in required_items
        ),
        "manual_testing_required": any("manual_test" in (item.get("operator_input_types") or []) for item in required_items),
        "target_path_required": any(
            "operator_selected_path" in (item.get("operator_input_types") or []) for item in required_items
        ),
        "host_mutation_approval_required": any(
            "host_admin_action" in (item.get("operator_input_types") or []) for item in required_items
        ),
        "all_remaining_items_can_be_deferred_with_operator_decision": all(item["can_defer"] for item in required_items),
    }


def _write_report(
    *,
    vault: Path,
    report: dict[str, Any],
    report_root: str | Path | None,
    report_slug: str | None,
) -> dict[str, Any]:
    report_dir = _resolve_report_root(vault, report_root)
    report_dir.mkdir(parents=True, exist_ok=True)
    slug = _safe_slug(report_slug)
    json_path = report_dir / f"{slug}.json"
    markdown_path = report_dir / f"{slug}.md"
    written = {
        "written": True,
        "json_path": _relative_to_vault(vault, json_path),
        "markdown_path": _relative_to_vault(vault, markdown_path),
    }
    report["evidence"] = written
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_path.write_text(format_studio_mvp_deferral_closeout_audit(report) + "\n", encoding="utf-8")
    return written


def build_studio_mvp_deferral_closeout_audit(
    vault_root: str | Path,
    *,
    approval_packet_id: str | None = None,
    write_report: bool = False,
    report_root: str | Path | None = None,
    report_slug: str | None = None,
) -> dict[str, Any]:
    """Build the read-only Studio MVP closeout/deferral audit."""

    vault = _vault_path(vault_root)
    packet_id = approval_packet_id or DEFAULT_APPROVAL_PACKET_ID
    pass10b = build_pass10b_expansion_pack_completion_audit(vault, approval_packet_id=packet_id)
    items = _mvp_items(pass10b)
    operator_summary = _operator_summary(items)
    authority = _authority()
    remaining_open = [item for item in items if item["operator_required"]]
    mvp_closed = False

    report: dict[str, Any] = {
        "ok": True,
        "closed": mvp_closed,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": STATUS,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "objective_restated": (
            "Audit the Studio MVP tail after Pass 10B installer-build proof and make every remaining "
            "operator-required credential, environment, approval, target-path, host-mutation, and manual-test dependency explicit."
        ),
        "summary": {
            "mvp_closed": mvp_closed,
            "studio_mvp_status": STATUS,
            "pass10b_installer_zip_proof_complete": _installer_zip_proof_complete(pass10b),
            "operator_human_in_loop_required": True,
            "remaining_operator_required_count": len(remaining_open),
            "remaining_open_item_count": len(remaining_open),
            "machine_can_continue_without_operator": False,
            "safe_autonomous_next_step_available": False,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
            **operator_summary,
        },
        "operator_human_in_loop_matrix": items,
        "operator_required_items": [item["id"] for item in remaining_open],
        "deferral_candidates": [
            {
                "id": item["id"],
                "title": item["title"],
                "deferral_requirement": item["deferral_requirement"],
            }
            for item in remaining_open
            if item["can_defer"]
        ],
        "must_not_be_auto_run": [
            "signing certificate/password/token handling",
            "provider/model calls",
            "browser control against real sessions or external targets",
            "runtime dispatch activation",
            "host startup/autostart mutation",
            "release promotion",
            "real target workspace migration",
            "manual install/launch acceptance",
        ],
        "authority": authority,
        "source_evidence": {
            "pass10b_expansion_pack_completion_audit": {
                "ok": pass10b.get("ok"),
                "complete": pass10b.get("complete"),
                "status": pass10b.get("status"),
                "summary": pass10b.get("summary"),
            }
        },
        "evidence": {
            "written": False,
            "json_path": None,
            "markdown_path": None,
        },
        "next_recommended_pass": NEXT_RECOMMENDED_PASS,
    }

    if write_report:
        _write_report(vault=vault, report=report, report_root=report_root, report_slug=report_slug)
    return report


def format_studio_mvp_deferral_closeout_audit(model: dict[str, Any]) -> str:
    summary = model.get("summary") or {}
    lines = [
        "Studio MVP Deferral Closeout Audit",
        f"  status: {model.get('status')}",
        f"  mvp_closed: {summary.get('mvp_closed')}",
        f"  pass10b_installer_zip_proof_complete: {summary.get('pass10b_installer_zip_proof_complete')}",
        f"  operator_human_in_loop_required: {summary.get('operator_human_in_loop_required')}",
        f"  remaining_operator_required_count: {summary.get('remaining_operator_required_count')}",
        f"  credential_or_secret_required: {summary.get('credential_or_secret_required')}",
        f"  environment_variable_required: {summary.get('environment_variable_required')}",
        f"  manual_testing_required: {summary.get('manual_testing_required')}",
        f"  target_path_required: {summary.get('target_path_required')}",
        f"  host_mutation_approval_required: {summary.get('host_mutation_approval_required')}",
        f"  next: {summary.get('next_recommended_pass')}",
        "",
        "Operator-required items:",
    ]
    for item in model.get("operator_human_in_loop_matrix") or []:
        if not item.get("operator_required"):
            continue
        lines.extend(
            [
                f"- {item.get('id')}: {item.get('status')}",
                f"  input: {', '.join(item.get('operator_input_types') or [])}",
                f"  action: {item.get('operator_action')}",
                f"  defer: {item.get('deferral_requirement')}",
            ]
        )
    lines.append("")
    lines.append(
        "Boundary: report-only audit; no approval consumption/execution, signing, secret reads, provider/model call, runtime/browser dispatch, host mutation, target mutation, release promotion, Agent Bus write, or canonical writeback."
    )
    evidence = model.get("evidence") or {}
    if evidence.get("written"):
        lines.append(f"Evidence: {evidence.get('markdown_path')}")
    return "\n".join(lines)
