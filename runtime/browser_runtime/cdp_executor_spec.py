"""No-execution CDP read-only proof executor specification."""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.browser_runtime.adapters.cdp_design import (
    CDPAdapterDesignRequest,
    evaluate_cdp_adapter_design,
)
from runtime.chaseos_gate import (
    BROWSER_CDP_READ_ONLY_PROOF_APPROVAL_SCHEMA_ID,
    BROWSER_CDP_READ_ONLY_PROOF_APPROVAL_REQUIRED_FIELDS,
    BROWSER_CDP_READ_ONLY_PROOF_OPERATION,
    check_runtime_operation,
    get_runtime_operation_approval_schema,
)


DEFAULT_LOCAL_TARGET_URL = "http://127.0.0.1:<port>"
DEFAULT_LOCAL_CDP_ENDPOINT = "http://127.0.0.1:<port>"
APPROVAL_RELATIVE_DIR = Path("07_LOGS/Agent-Activity/_bosl_cdp_approvals")
IDEMPOTENCY_MARKER_RELATIVE_DIR = APPROVAL_RELATIVE_DIR / "_execution_markers"
OPERATIONAL_ACTIVATION_BUILD_LOG_RELATIVE_PATH = Path(
    "07_LOGS/Build-Logs/2026-05-02-ChaseOS-hermes-browser-cdp-operational-environment-activation.md"
)
APPROVAL_STATUSES = {"pending", "approved", "denied", "revoked", "expired"}
_SAFE_GATE_APPROVAL_ID = re.compile(r"^[A-Za-z0-9_.-]+$")


class BrowserCDPExecutorSpecError(RuntimeError):
    """Raised when a no-execution CDP executor-spec request is invalid."""


def build_cdp_read_only_executor_spec(
    *,
    vault_root: str | Path | None = None,
    target_url: str | None = None,
    cdp_endpoint: str | None = None,
    allowed_domains: list[str] | None = None,
    runtime: str = "unknown",
    gate_approval_id: str | None = None,
    source_command: str = "chaseos runtime browser-cdp executor-spec",
) -> dict[str, Any]:
    """Return the fail-closed executor spec for a future CDP read-only proof."""
    if gate_approval_id and not _SAFE_GATE_APPROVAL_ID.match(gate_approval_id):
        raise BrowserCDPExecutorSpecError(f"unsafe gate_approval_id: {gate_approval_id!r}")

    target = target_url or DEFAULT_LOCAL_TARGET_URL
    endpoint = cdp_endpoint or DEFAULT_LOCAL_CDP_ENDPOINT
    domains = allowed_domains or _allowed_domains_for_target(target)

    schema = get_runtime_operation_approval_schema(
        BROWSER_CDP_READ_ONLY_PROOF_OPERATION,
        runtime=runtime,
        external_api="browser.navigation",
        source_command=source_command,
    )
    gate_allowed, gate_reason = check_runtime_operation(
        BROWSER_CDP_READ_ONLY_PROOF_OPERATION,
        external_api="browser.navigation",
        write_targets=[
            "07_LOGS/Browser-Runs/future-cdp-read-only-proof.json",
            "07_LOGS/Agent-Activity/future-cdp-read-only-proof.md",
            "03_INPUTS/Browser-Skill-Candidates/future/future-cdp-read-only-proof.md",
        ],
    )

    design = evaluate_cdp_adapter_design(
        CDPAdapterDesignRequest(
            cdp_endpoint=endpoint,
            target_url=target,
            allowed_domains=domains,
            mode="read_only",
            allowed_actions=[
                "page.navigate",
                "page.capture_screenshot",
                "dom.snapshot",
                "page.read_title",
                "page.read_url",
                "page.read_visible_text",
                "wait_for",
            ],
        )
    )

    approval_validation = validate_cdp_read_only_approval_artifact(
        vault_root,
        gate_approval_id,
        expected_target_url=target,
        expected_runtime=runtime,
    )
    artifact_supplied = bool(gate_approval_id)
    artifact_valid = bool(approval_validation.get("structurally_valid"))
    preconditions = [
        _precondition(
            "executor_implemented",
            passed=True,
            status="passed",
            reason="CDP read-only proof executor is implemented behind approval and idempotency gates",
        ),
        _precondition(
            "gate_operation_declared",
            passed=schema is not None,
            status="passed" if schema else "failed",
            reason="Gate approval schema is visible" if schema else "Gate approval schema is missing",
            evidence={"approval_schema_id": (schema or {}).get("approval_schema_id")},
        ),
        _precondition(
            "gate_execution_allowed",
            passed=gate_allowed,
            status="passed" if gate_allowed else "blocked",
            reason=gate_reason,
        ),
        _precondition(
            "approval_artifact_supplied",
            passed=artifact_supplied,
            status="passed" if artifact_supplied else "missing",
            reason="gate_approval_id supplied" if artifact_supplied else "no gate_approval_id supplied",
        ),
        _precondition(
            "approval_artifact_store_implemented",
            passed=True,
            status="passed",
            reason="CDP approval artifact persistence/lookup is implemented for pending request records",
        ),
        _precondition(
            "approval_artifact_structurally_valid",
            passed=artifact_valid,
            status=("passed" if artifact_valid else ("failed" if artifact_supplied else "not_checked")),
            reason=str(approval_validation.get("reason") or "approval artifact not checked"),
            evidence={"gate_approval_id": gate_approval_id} if gate_approval_id else {},
        ),
        _precondition(
            "approval_status_approved",
            passed=str(approval_validation.get("approval_status") or "") == "approved",
            status=str(approval_validation.get("approval_status") or "not_checked"),
            reason="approval status must be approved before execution",
        ),
        _precondition(
            "approval_decision_consumption_implemented",
            passed=True,
            status="passed",
            reason="immutable approval decision consumption is implemented for CDP proofs",
        ),
        _precondition(
            "cdp_design_preflight_passed",
            passed=bool(design.get("ok")),
            status="passed" if design.get("ok") else "blocked",
            reason=str(design.get("status")),
            evidence={"blockers": design.get("blockers", [])},
        ),
        _precondition(
            "browser_launcher_implemented",
            passed=True,
            status="passed",
            reason="isolated throwaway browser launcher is implemented for this CDP proof",
        ),
        _precondition(
            "cdp_client_implemented",
            passed=True,
            status="passed",
            reason="minimal local CDP client/socket connection is implemented for this proof",
        ),
        _precondition(
            "secret_cookie_profile_exclusion_declared",
            passed=True,
            status="passed",
            reason="schema and design preflight keep credentials, cookies, sessions, and real profiles disabled",
        ),
        _precondition(
            "artifact_targets_limited",
            passed=True,
            status="passed",
            reason="future outputs remain limited to browser run logs, agent activity, and untrusted candidates",
        ),
    ]

    blocked_reasons = [
        item["precondition_id"]
        for item in preconditions
        if not item["passed"] and item["status"] in {"blocked", "missing", "not_built", "failed", "not_checked"}
    ]

    return {
        "ok": True,
        "operation": BROWSER_CDP_READ_ONLY_PROOF_OPERATION,
        "approval_schema_id": BROWSER_CDP_READ_ONLY_PROOF_APPROVAL_SCHEMA_ID,
        "executor_status": "implemented",
        "execution_enabled": bool(gate_allowed and artifact_valid and approval_validation.get("approval_status") == "approved"),
        "cdp_read_only_proof_allowed": bool(gate_allowed and artifact_valid and approval_validation.get("approval_status") == "approved"),
        "browser_launch_attempted": False,
        "cdp_connection_attempted": False,
        "screenshot_attempted": False,
        "dom_snapshot_attempted": False,
        "credential_value_read": False,
        "cookie_or_session_read": False,
        "real_profile_used": False,
        "trusted_skill_written": False,
        "canonical_files_mutated": False,
        "approval_request_written": False,
        "files_modified": False,
        "runtime": runtime,
        "target_url": target,
        "cdp_endpoint": endpoint,
        "allowed_domains": domains,
        "gate_policy": {"allowed": gate_allowed, "reason": gate_reason},
        "approval_schema": schema,
        "approval_validation": approval_validation,
        "cdp_design_preflight": design,
        "preconditions": preconditions,
        "blocked_reasons": blocked_reasons,
        "future_executor_requirements": [
            "persist a pending CDP proof approval request before any execution pass",
            "validate approval artifact shape and immutable approval decision provenance",
            "require approved status plus an approval-aware Gate runtime operation check",
            "launch only a ChaseOS-created isolated browser context",
            "connect only to a local CDP endpoint bound to 127.0.0.1, localhost, or ::1",
            "limit actions to navigate, visible read, title/url read, DOM snapshot, screenshot, and wait",
            "write only browser run logs, agent activity, screenshots, and untrusted candidates",
            "persist a single-attempt idempotency marker per gate_approval_id before execution",
            "never read credentials, cookies, session tokens, real profile state, browser history, or raw CDP passthrough",
            "never write trusted skills, activate skills, enqueue Agent Bus tasks, call providers, or mutate canonical docs",
        ],
        "source_command": source_command,
    }


def build_cdp_read_only_closeout_readiness_report(
    *,
    vault_root: str | Path | None = None,
    target_url: str | None = None,
    cdp_endpoint: str | None = None,
    runtime: str = "unknown",
    gate_approval_id: str | None = None,
    source_command: str = "chaseos runtime browser-cdp closeout-readiness",
) -> dict[str, Any]:
    """Return a no-execution closure/readiness report for the Browser CDP path."""
    executor_spec = build_cdp_read_only_executor_spec(
        vault_root=vault_root,
        target_url=target_url,
        cdp_endpoint=cdp_endpoint,
        runtime=runtime,
        gate_approval_id=gate_approval_id,
        source_command=source_command,
    )
    gate_id = gate_approval_id or "browser-cdp-closeout-readiness"
    decision_policy = build_cdp_read_only_approval_decision_policy(
        vault_root or Path.cwd(),
        gate_id,
        target_url=target_url,
        cdp_endpoint=cdp_endpoint,
        runtime=runtime,
        source_command=source_command,
    )
    consumer_design = build_cdp_read_only_approval_decision_consumer_design(
        vault_root or Path.cwd(),
        gate_id,
        target_url=target_url,
        cdp_endpoint=cdp_endpoint,
        runtime=runtime,
        source_command=source_command,
    )
    marker_design = build_cdp_read_only_atomic_marker_writer_design(
        vault_root or Path.cwd(),
        gate_id,
        target_url=target_url,
        cdp_endpoint=cdp_endpoint,
        runtime=runtime,
        source_command=source_command,
    )
    launcher_design = build_cdp_read_only_isolated_browser_launcher_design(
        vault_root or Path.cwd(),
        gate_id,
        target_url=target_url,
        cdp_endpoint=cdp_endpoint,
        runtime=runtime,
        source_command=source_command,
    )
    launcher_preflight = build_cdp_read_only_isolated_launcher_implementation_preflight(
        vault_root or Path.cwd(),
        gate_id,
        target_url=target_url,
        cdp_endpoint=cdp_endpoint,
        runtime=runtime,
        source_command=source_command,
    )
    activation_evidence = _browser_cdp_operational_activation_evidence(vault_root or Path.cwd())
    operationally_activated = bool(activation_evidence.get("operationally_activated"))
    verified_no_execution_surfaces = [
        {"surface": "approval-request", "status": "verified_request_only"},
        {"surface": "approval-artifact-validation", "status": "verified_no_consumption"},
        {"surface": "executor-spec", "status": "verified_executor_implemented_non_executing_spec"},
        {"surface": "decision-preflight", "status": "verified_no_consumption"},
        {"surface": "idempotency-reservation-spec", "status": "verified_no_marker_write"},
        {"surface": "executor-dry-run", "status": "verified_no_execution"},
        {"surface": "browser-cdp-execute", "status": "verified_injected_executor_only"},
        {"surface": "approval-decision-policy", "status": "verified_no_consumption"},
        {"surface": "approval-decision-consumer-design", "status": "verified_no_consumption"},
        {"surface": "atomic-marker-writer-design", "status": "verified_no_marker_write"},
        {"surface": "isolated-browser-launcher-design", "status": "verified_no_launch"},
        {"surface": "isolated-launcher-implementation-preflight", "status": "verified_no_launch"},
        {
            "surface": "closeout-readiness",
            "status": (
                "verified_feature_implemented_operationally_activated"
                if operationally_activated
                else "verified_feature_implemented_environment_smoke_blocked"
            ),
        },
    ]
    implementation_blockers = [] if operationally_activated else [
        "local_chromium_executable_not_configured_for_smoke",
        "real_environment_smoke_not_passed",
    ]
    closeout_status = (
        "browser_cdp_bounded_read_only_proof_implemented_and_operationally_activated"
        if operationally_activated
        else "browser_cdp_feature_implemented_environment_smoke_blocked"
    )
    closure_recommendation = (
        "Close the bounded Browser CDP implementation and operational activation thread for the approved "
        "read-only proof path. Future work should target product-specific proofs, skill learning, and broader "
        "Browser Runtime gaps without reopening the CDP launcher implementation."
        if operationally_activated
        else (
            "Close the bounded Browser CDP implementation thread as code-complete for the approval-gated "
            "read-only proof path. Local operational readiness still requires configuring a Chromium-compatible "
            "browser executable and passing the real-environment smoke."
        )
    )
    return {
        "ok": True,
        "schema_version": 1,
        "operation": BROWSER_CDP_READ_ONLY_PROOF_OPERATION,
        "approval_schema_id": BROWSER_CDP_READ_ONLY_PROOF_APPROVAL_SCHEMA_ID,
        "closeout_status": closeout_status,
        "feature_closed_for_live_execution": True,
        "operational_activation_status": (
            "activated_for_bounded_read_only_proof" if operationally_activated else "activation_evidence_missing"
        ),
        "local_environment_smoke_passed": operationally_activated,
        "operational_activation_evidence": activation_evidence,
        "pre_execution_governance_thread_closeable": True,
        "execution_enabled": False,
        "cdp_read_only_proof_allowed": False,
        "browser_launch_attempted": False,
        "cdp_connection_attempted": False,
        "screenshot_attempted": False,
        "dom_snapshot_attempted": False,
        "approval_consumed": False,
        "approval_artifact_mutated": False,
        "approval_decision_written": False,
        "idempotency_marker_written": False,
        "trusted_skill_written": False,
        "canonical_files_mutated": False,
        "agent_bus_task_enqueued": False,
        "provider_call_attempted": False,
        "files_modified": False,
        "runtime": runtime,
        "target_url": target_url or DEFAULT_LOCAL_TARGET_URL,
        "cdp_endpoint": cdp_endpoint or DEFAULT_LOCAL_CDP_ENDPOINT,
        "verified_no_execution_surfaces": verified_no_execution_surfaces,
        "implementation_blockers": implementation_blockers,
        "closure_recommendation": closure_recommendation,
        "executor_spec": executor_spec,
        "approval_decision_policy": decision_policy,
        "approval_decision_consumer_design": consumer_design,
        "atomic_marker_writer_design": marker_design,
        "isolated_browser_launcher_design": launcher_design,
        "isolated_launcher_implementation_preflight": launcher_preflight,
        "source_command": source_command,
    }


def format_cdp_closeout_readiness_report(payload: dict[str, Any]) -> str:
    lines = ["ChaseOS Browser CDP Closeout Readiness"]
    lines.append(f"closeout_status: {payload.get('closeout_status')}")
    lines.append(f"pre_execution_governance_thread_closeable: {payload.get('pre_execution_governance_thread_closeable')}")
    lines.append(f"feature_closed_for_live_execution: {payload.get('feature_closed_for_live_execution')}")
    lines.append(f"operational_activation_status: {payload.get('operational_activation_status')}")
    lines.append(f"local_environment_smoke_passed: {payload.get('local_environment_smoke_passed')}")
    lines.append(f"execution_enabled: {payload.get('execution_enabled')}")
    lines.append(f"browser_launch_attempted: {payload.get('browser_launch_attempted')}")
    lines.append(f"cdp_connection_attempted: {payload.get('cdp_connection_attempted')}")
    lines.append(f"approval_consumed: {payload.get('approval_consumed')}")
    lines.append(f"idempotency_marker_written: {payload.get('idempotency_marker_written')}")
    lines.append("verified_no_execution_surfaces:")
    for item in payload.get("verified_no_execution_surfaces") or []:
        lines.append(f"- {item.get('surface')}: {item.get('status')}")
    blockers = payload.get("implementation_blockers") or []
    if blockers:
        lines.append("implementation_blockers:")
        for blocker in blockers:
            lines.append(f"- {blocker}")
    lines.append(f"closure_recommendation: {payload.get('closure_recommendation')}")
    return "\n".join(lines)


def format_cdp_executor_spec(payload: dict[str, Any]) -> str:
    """Return a compact human-readable executor-spec summary."""
    lines = ["ChaseOS Browser CDP Read-Only Executor Spec"]
    lines.append(f"ok: {payload.get('ok')}")
    lines.append(f"executor_status: {payload.get('executor_status')}")
    lines.append(f"execution_enabled: {payload.get('execution_enabled')}")
    lines.append(f"cdp_read_only_proof_allowed: {payload.get('cdp_read_only_proof_allowed')}")
    lines.append(f"browser_launch_attempted: {payload.get('browser_launch_attempted')}")
    lines.append(f"cdp_connection_attempted: {payload.get('cdp_connection_attempted')}")
    lines.append(f"credential_value_read: {payload.get('credential_value_read')}")
    lines.append(f"cookie_or_session_read: {payload.get('cookie_or_session_read')}")
    lines.append(f"trusted_skill_written: {payload.get('trusted_skill_written')}")
    lines.append(f"canonical_files_mutated: {payload.get('canonical_files_mutated')}")
    gate = payload.get("gate_policy") or {}
    lines.append(f"gate_allowed: {gate.get('allowed')}")
    lines.append(f"gate_reason: {gate.get('reason')}")
    blocked = payload.get("blocked_reasons") or []
    if blocked:
        lines.append("blocked_reasons:")
        for reason in blocked:
            lines.append(f"- {reason}")
    preconditions = payload.get("preconditions") or []
    if preconditions:
        lines.append("preconditions:")
        for item in preconditions:
            lines.append(f"- {item.get('precondition_id')}: {item.get('status')} - {item.get('reason')}")
    return "\n".join(lines)


def build_cdp_read_only_decision_preflight(
    vault_root: str | Path,
    gate_approval_id: str,
    *,
    target_url: str | None = None,
    cdp_endpoint: str | None = None,
    runtime: str = "unknown",
    source_command: str | None = None,
) -> dict[str, Any]:
    """Inspect approval consumption prerequisites without consuming approval."""
    _validate_gate_approval_id(gate_approval_id)
    spec = build_cdp_read_only_executor_spec(
        vault_root=vault_root,
        target_url=target_url,
        cdp_endpoint=cdp_endpoint,
        runtime=runtime,
        gate_approval_id=gate_approval_id,
        source_command=source_command or "chaseos runtime browser-cdp decision-preflight",
    )
    validation = spec.get("approval_validation") if isinstance(spec.get("approval_validation"), dict) else {}
    marker_path = cdp_read_only_idempotency_marker_path(vault_root, gate_approval_id)
    marker_exists = marker_path.exists()
    approval_status = str(validation.get("approval_status") or "missing")
    structurally_valid = bool(validation.get("structurally_valid"))
    matches_preflight = bool(validation.get("matches_preflight"))
    write_plan = _future_cdp_write_plan(spec, gate_approval_id)
    write_plan_limited = _future_write_plan_is_limited(write_plan)

    if not structurally_valid:
        decision_status = "blocked_approval_artifact_invalid"
        next_action = "operator_must_recreate_or_fix_browser_cdp_approval_artifact"
    elif marker_exists:
        decision_status = "blocked_prior_cdp_proof_marker_exists"
        next_action = "operator_must_review_existing_cdp_proof_marker_before_any_retry"
    elif approval_status != "approved":
        decision_status = "blocked_approval_not_approved"
        next_action = "operator_or_gate_must_mark_artifact_approved_before_future_executor"
    else:
        decision_status = "approved_artifact_valid_executor_ready"
        next_action = "execute_browser_cdp_read_only_proof"

    preconditions = [
        _precondition(
            "approval_artifact_structurally_valid",
            passed=structurally_valid,
            status="passed" if structurally_valid else "blocked",
            reason=str(validation.get("reason") or "approval artifact validation failed"),
            evidence={"artifact_ref": validation.get("artifact_ref")},
        ),
        _precondition(
            "approval_status_approved",
            passed=approval_status == "approved",
            status=approval_status,
            reason="approval artifact status must be approved before any future executor can run",
        ),
        _precondition(
            "approval_artifact_matches_executor_spec",
            passed=matches_preflight,
            status="passed" if matches_preflight else "blocked",
            reason="approval artifact must match requested target/runtime preflight",
        ),
        _precondition(
            "idempotency_marker_absent",
            passed=not marker_exists,
            status="absent" if not marker_exists else "present",
            reason="one future execution attempt must reserve an idempotency marker before browser/CDP work",
            evidence={"marker_path": str(marker_path)},
        ),
        _precondition(
            "future_write_plan_limited",
            passed=write_plan_limited,
            status="passed" if write_plan_limited else "blocked",
            reason="future writes must stay in declared log, screenshot, and untrusted-candidate surfaces",
        ),
        _precondition(
            "approval_decision_consumption_implemented",
            passed=False,
            status="not_built",
            reason="immutable approval decision consumption is not implemented for CDP proofs",
        ),
        _precondition(
            "browser_launcher_implemented",
            passed=False,
            status="not_built",
            reason="isolated browser launcher is not implemented for this proof",
        ),
        _precondition(
            "cdp_client_implemented",
            passed=False,
            status="not_built",
            reason="CDP client/socket connection is not implemented for this proof",
        ),
    ]
    blocked_reasons: list[str] = []
    if not structurally_valid:
        blocked_reasons.append("browser_cdp_approval_artifact_invalid")
    if approval_status != "approved":
        blocked_reasons.append("browser_cdp_approval_not_approved")
    if marker_exists:
        blocked_reasons.append("browser_cdp_idempotency_marker_exists")
    if not write_plan_limited:
        blocked_reasons.append("browser_cdp_future_write_plan_not_limited")

    return {
        "ok": True,
        "schema_version": 1,
        "operation": BROWSER_CDP_READ_ONLY_PROOF_OPERATION,
        "approval_schema_id": BROWSER_CDP_READ_ONLY_PROOF_APPROVAL_SCHEMA_ID,
        "gate_approval_id": gate_approval_id,
        "decision_consumption_status": decision_status,
        "executor_status": "implemented",
        "execution_enabled": approval_status == "approved" and structurally_valid and matches_preflight and not marker_exists and write_plan_limited,
        "cdp_read_only_proof_allowed": approval_status == "approved" and structurally_valid and matches_preflight and not marker_exists and write_plan_limited,
        "approval_status": approval_status,
        "approval_status_approved": approval_status == "approved",
        "approval_decision_accepted": False,
        "approval_validation": validation,
        "executor_spec": spec,
        "idempotency": {
            "marker_path": str(marker_path),
            "marker_exists": marker_exists,
            "status": "prior_cdp_proof_marker_exists_blocked" if marker_exists else "no_prior_cdp_proof_marker",
            "future_marker_write_required_before_any_browser_action": True,
        },
        "future_write_plan": write_plan,
        "preconditions": preconditions,
        "blocked_reasons": blocked_reasons,
        "approval_consumed": False,
        "approval_artifact_mutated": False,
        "approval_request_written": False,
        "browser_launch_attempted": False,
        "cdp_connection_attempted": False,
        "screenshot_attempted": False,
        "dom_snapshot_attempted": False,
        "credential_value_read": False,
        "cookie_or_session_read": False,
        "real_profile_used": False,
        "trusted_skill_written": False,
        "canonical_files_mutated": False,
        "agent_bus_task_enqueued": False,
        "provider_call_attempted": False,
        "files_modified": False,
        "next_action": next_action,
        "source_command": source_command,
    }


def build_cdp_read_only_idempotency_reservation_spec(
    vault_root: str | Path,
    gate_approval_id: str,
    *,
    target_url: str | None = None,
    cdp_endpoint: str | None = None,
    runtime: str = "unknown",
    source_command: str | None = None,
) -> dict[str, Any]:
    """Return the future CDP proof idempotency reservation contract without writing it."""
    _validate_gate_approval_id(gate_approval_id)
    preflight = build_cdp_read_only_decision_preflight(
        vault_root,
        gate_approval_id,
        target_url=target_url,
        cdp_endpoint=cdp_endpoint,
        runtime=runtime,
        source_command=source_command or "chaseos runtime browser-cdp idempotency-reservation-spec",
    )
    validation = (
        preflight.get("approval_validation")
        if isinstance(preflight.get("approval_validation"), dict)
        else {}
    )
    idempotency = preflight.get("idempotency") if isinstance(preflight.get("idempotency"), dict) else {}
    marker_path = cdp_read_only_idempotency_marker_path(vault_root, gate_approval_id)
    marker_exists = bool(idempotency.get("marker_exists"))
    approval_status = str(preflight.get("approval_status") or "missing")
    structurally_valid = bool(validation.get("structurally_valid"))
    matches_preflight = bool(validation.get("matches_preflight"))
    future_write_plan = (
        preflight.get("future_write_plan")
        if isinstance(preflight.get("future_write_plan"), dict)
        else {}
    )

    if not structurally_valid:
        reservation_status = "blocked_approval_artifact_invalid"
        next_action = "operator_must_recreate_or_fix_browser_cdp_approval_artifact"
    elif marker_exists:
        reservation_status = "blocked_prior_cdp_proof_marker_exists"
        next_action = "operator_must_review_existing_cdp_proof_marker_before_any_retry"
    elif approval_status != "approved":
        reservation_status = "blocked_approval_not_approved"
        next_action = "operator_or_gate_must_mark_artifact_approved_before_future_marker_reservation"
    elif not matches_preflight:
        reservation_status = "blocked_approval_artifact_does_not_match_preflight"
        next_action = "operator_must_reissue_approval_for_current_target_and_runtime"
    else:
        reservation_status = "ready_for_future_marker_reservation_but_writer_not_built"
        next_action = "implement_atomic_marker_writer_only_after_approval_consumption_policy"

    marker_record_template = {
        "record_type": "browser_cdp_read_only_proof_idempotency_marker",
        "schema_version": 1,
        "operation": BROWSER_CDP_READ_ONLY_PROOF_OPERATION,
        "approval_schema_id": BROWSER_CDP_READ_ONLY_PROOF_APPROVAL_SCHEMA_ID,
        "gate_approval_id": gate_approval_id,
        "target_url": str(preflight.get("target_url") or target_url or DEFAULT_LOCAL_TARGET_URL),
        "runtime": runtime,
        "status": "reserved",
        "reserved_at": "<future-runtime-utc>",
        "attempt_id": "<future-single-attempt-id>",
        "source_approval_artifact_ref": validation.get("artifact_ref"),
        "source_approval_request_digest_sha256": validation.get("request_digest_sha256"),
        "future_write_plan": future_write_plan,
        "browser_launch_attempted": False,
        "cdp_connection_attempted": False,
        "screenshot_attempted": False,
        "dom_snapshot_attempted": False,
        "credential_value_read": False,
        "cookie_or_session_read": False,
        "real_profile_used": False,
        "trusted_skill_written": False,
        "canonical_files_mutated": False,
        "agent_bus_task_enqueued": False,
        "provider_call_attempted": False,
    }

    return {
        "ok": True,
        "schema_version": 1,
        "operation": BROWSER_CDP_READ_ONLY_PROOF_OPERATION,
        "approval_schema_id": BROWSER_CDP_READ_ONLY_PROOF_APPROVAL_SCHEMA_ID,
        "gate_approval_id": gate_approval_id,
        "reservation_status": reservation_status,
        "executor_status": "implemented",
        "execution_enabled": approval_status == "approved" and structurally_valid and matches_preflight and not marker_exists,
        "cdp_read_only_proof_allowed": approval_status == "approved" and structurally_valid and matches_preflight and not marker_exists,
        "approval_status": approval_status,
        "approval_status_approved": approval_status == "approved",
        "approval_decision_accepted": False,
        "approval_validation": validation,
        "decision_preflight": preflight,
        "idempotency": {
            "marker_path": str(marker_path),
            "marker_exists": marker_exists,
            "marker_exists_before": marker_exists,
            "idempotency_marker_written": False,
            "future_marker_write_required_before_any_browser_action": True,
            "future_marker_write_mode": "atomic_create_new_only",
        },
        "marker_record_template": marker_record_template,
        "reservation_rules": [
            "validate approval artifact immediately before any future marker write",
            "marker write must be atomic and create-new only",
            "marker is single-use per gate_approval_id",
            "marker must be written before browser launch or CDP connection",
            "if a later proof fails, write failure evidence and do not delete the marker",
            "no retry is allowed without operator review and a new approval/reservation decision",
            "marker payload must not contain credentials, cookies, session tokens, browser storage, or profile paths",
        ],
        "blocked_reasons": list(dict.fromkeys(preflight.get("blocked_reasons") or [])),
        "approval_consumed": False,
        "approval_artifact_mutated": False,
        "approval_request_written": False,
        "idempotency_marker_written": False,
        "browser_launch_attempted": False,
        "cdp_connection_attempted": False,
        "screenshot_attempted": False,
        "dom_snapshot_attempted": False,
        "credential_value_read": False,
        "cookie_or_session_read": False,
        "real_profile_used": False,
        "trusted_skill_written": False,
        "canonical_files_mutated": False,
        "agent_bus_task_enqueued": False,
        "provider_call_attempted": False,
        "files_modified": False,
        "next_action": next_action,
        "source_command": source_command,
    }


def write_cdp_read_only_approval_decision(
    vault_root: str | Path,
    gate_approval_id: str,
    *,
    approved_by: str,
    decision_status: str = "approved",
) -> dict[str, Any]:
    """Record an operator/Gate approval decision for one Browser CDP proof request."""
    _validate_gate_approval_id(gate_approval_id)
    if decision_status not in {"approved", "denied", "revoked", "expired"}:
        raise BrowserCDPExecutorSpecError(f"unsupported approval decision status: {decision_status}")
    path = _approval_artifact_path(vault_root, gate_approval_id)
    if not path.exists():
        raise BrowserCDPExecutorSpecError(f"CDP approval request not found: {gate_approval_id}")
    record = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(record, dict):
        raise BrowserCDPExecutorSpecError("CDP approval request must be a JSON object")
    if record.get("gate_approval_id") != gate_approval_id:
        raise BrowserCDPExecutorSpecError("CDP approval request gate_approval_id mismatch")
    if record.get("status") not in {"pending", decision_status}:
        raise BrowserCDPExecutorSpecError(f"CDP approval request already has terminal status: {record.get('status')}")
    decided_at = _utc_now()
    record.update(
        {
            "status": decision_status,
            "approved_by": str(approved_by) if decision_status == "approved" else None,
            "approved_at": decided_at if decision_status == "approved" else None,
            "decision_status": decision_status,
            "decision_id": f"bosl-cdp-decision-{uuid.uuid4().hex[:12]}",
            "decided_by": str(approved_by),
            "decided_at": decided_at,
            "approval_decision_written": True,
            "approval_consumed": False,
        }
    )
    record["request_digest_sha256"] = _approval_digest(record)
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    decision_dir = approval_artifacts_dir(vault_root) / "_decisions"
    decision_dir.mkdir(parents=True, exist_ok=True)
    decision_path = decision_dir / f"{gate_approval_id}.json"
    decision_payload = {
        "record_type": "browser_cdp_read_only_proof_approval_decision",
        "schema_version": 1,
        "operation": BROWSER_CDP_READ_ONLY_PROOF_OPERATION,
        "approval_schema_id": BROWSER_CDP_READ_ONLY_PROOF_APPROVAL_SCHEMA_ID,
        "gate_approval_id": gate_approval_id,
        "decision_status": decision_status,
        "decided_by": str(approved_by),
        "decided_at": decided_at,
        "source_approval_artifact_ref": str(path),
        "request_digest_sha256": record["request_digest_sha256"],
    }
    decision_path.write_text(json.dumps(decision_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    validation = validate_cdp_read_only_approval_artifact(
        vault_root,
        gate_approval_id,
        expected_target_url=str(record.get("target_url") or ""),
        expected_runtime=str(record.get("runtime") or ""),
    )
    return {
        "ok": validation.get("structurally_valid") is True and validation.get("approval_status") == decision_status,
        "approval_decision_written": True,
        "approval_decision_ref": str(decision_path),
        "approval_ref": str(path),
        "gate_approval_id": gate_approval_id,
        "approval_status": validation.get("approval_status"),
        "approval_validation": validation,
        "browser_launch_attempted": False,
        "cdp_connection_attempted": False,
        "idempotency_marker_written": False,
    }


def _consume_cdp_read_only_approval_decision(
    vault_root: str | Path,
    gate_approval_id: str,
    *,
    expected_target_url: str,
    expected_runtime: str,
) -> dict[str, Any]:
    validation = validate_cdp_read_only_approval_artifact(
        vault_root,
        gate_approval_id,
        expected_target_url=expected_target_url,
        expected_runtime=expected_runtime,
    )
    if not validation.get("structurally_valid"):
        return {"ok": False, "status": "blocked_approval_artifact_invalid", "approval_validation": validation}
    if validation.get("approval_status") != "approved":
        return {"ok": False, "status": "blocked_approval_not_approved", "approval_validation": validation}
    if not validation.get("approved_by") or not validation.get("approved_at"):
        return {"ok": False, "status": "blocked_approval_decision_metadata_missing", "approval_validation": validation}
    path = approval_artifacts_dir(vault_root) / "_consumptions" / f"{gate_approval_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "record_type": "browser_cdp_read_only_proof_approval_consumption",
        "schema_version": 1,
        "operation": BROWSER_CDP_READ_ONLY_PROOF_OPERATION,
        "approval_schema_id": BROWSER_CDP_READ_ONLY_PROOF_APPROVAL_SCHEMA_ID,
        "gate_approval_id": gate_approval_id,
        "consumed_at": _utc_now(),
        "consumed_by": expected_runtime,
        "source_approval_artifact_ref": validation.get("artifact_ref"),
        "source_approval_request_digest_sha256": validation.get("request_digest_sha256"),
    }
    try:
        with path.open("x", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    except FileExistsError:
        return {"ok": False, "status": "blocked_approval_already_consumed", "approval_validation": validation, "consumption_ref": str(path)}
    return {"ok": True, "status": "approval_consumed", "approval_validation": validation, "consumption_ref": str(path), "record": payload}


def _write_cdp_idempotency_marker(
    vault_root: str | Path,
    gate_approval_id: str,
    *,
    target_url: str,
    runtime: str,
    consumption_ref: str,
) -> dict[str, Any]:
    marker_path = cdp_read_only_idempotency_marker_path(vault_root, gate_approval_id)
    marker_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "record_type": "browser_cdp_read_only_proof_idempotency_marker",
        "schema_version": 1,
        "operation": BROWSER_CDP_READ_ONLY_PROOF_OPERATION,
        "approval_schema_id": BROWSER_CDP_READ_ONLY_PROOF_APPROVAL_SCHEMA_ID,
        "gate_approval_id": gate_approval_id,
        "target_url": target_url,
        "runtime": runtime,
        "status": "reserved",
        "reserved_at": _utc_now(),
        "attempt_id": f"bosl-cdp-attempt-{uuid.uuid4().hex[:12]}",
        "consumption_ref": consumption_ref,
        "browser_launch_attempted": False,
        "cdp_connection_attempted": False,
        "screenshot_attempted": False,
        "dom_snapshot_attempted": False,
        "credential_value_read": False,
        "cookie_or_session_read": False,
        "real_profile_used": False,
        "trusted_skill_written": False,
        "canonical_files_mutated": False,
        "agent_bus_task_enqueued": False,
        "provider_call_attempted": False,
    }
    try:
        with marker_path.open("x", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    except FileExistsError:
        return {"ok": False, "status": "blocked_prior_cdp_proof_marker_exists", "marker_ref": str(marker_path)}
    return {"ok": True, "status": "idempotency_marker_written", "marker_ref": str(marker_path), "record": payload}


def execute_cdp_read_only_proof(
    vault_root: str | Path,
    gate_approval_id: str,
    *,
    target_url: str,
    runtime: str = "unknown",
    launcher: Any | None = None,
    cdp_client: Any | None = None,
    source_command: str = "chaseos runtime browser-cdp execute",
) -> dict[str, Any]:
    """Execute one approved bounded local Browser CDP read-only proof."""
    _validate_gate_approval_id(gate_approval_id)
    marker_path = cdp_read_only_idempotency_marker_path(vault_root, gate_approval_id)
    if marker_path.exists():
        return {
            "ok": False,
            "status": "blocked_prior_cdp_proof_marker_exists",
            "idempotency_marker_ref": str(marker_path),
            "browser_launch_attempted": False,
            "cdp_connection_attempted": False,
            "screenshot_attempted": False,
            "dom_snapshot_attempted": False,
        }
    if launcher is None or cdp_client is None:
        from runtime.browser_runtime.cdp_live import BrowserCDPLiveError, IsolatedBrowserLauncher, MinimalCDPClient

        launcher = launcher or IsolatedBrowserLauncher()
        cdp_client = cdp_client or MinimalCDPClient()
    else:
        BrowserCDPLiveError = RuntimeError

    availability_check = getattr(launcher, "ensure_available", None)
    if callable(availability_check):
        try:
            availability_check()
        except Exception as exc:
            return {
                "ok": False,
                "status": "blocked_browser_executable_unavailable",
                "executor_status": "implemented",
                "approval_consumed": False,
                "idempotency_marker_written": False,
                "browser_launch_attempted": False,
                "cdp_connection_attempted": False,
                "screenshot_attempted": False,
                "dom_snapshot_attempted": False,
                "environment_blocker": str(exc),
            }

    consumption = _consume_cdp_read_only_approval_decision(
        vault_root,
        gate_approval_id,
        expected_target_url=target_url,
        expected_runtime=runtime,
    )
    if not consumption.get("ok"):
        return {
            "ok": False,
            "status": consumption.get("status"),
            "approval_consumed": False,
            "idempotency_marker_written": False,
            "browser_launch_attempted": False,
            "cdp_connection_attempted": False,
            "screenshot_attempted": False,
            "dom_snapshot_attempted": False,
            "approval_validation": consumption.get("approval_validation"),
        }
    marker = _write_cdp_idempotency_marker(
        vault_root,
        gate_approval_id,
        target_url=target_url,
        runtime=runtime,
        consumption_ref=str(consumption.get("consumption_ref")),
    )
    if not marker.get("ok"):
        return {
            "ok": False,
            "status": marker.get("status"),
            "approval_consumed": True,
            "consumption_ref": consumption.get("consumption_ref"),
            "idempotency_marker_written": False,
            "browser_launch_attempted": False,
            "cdp_connection_attempted": False,
        }

    launch_info: dict[str, Any] = {}
    screenshot_bytes = b""
    state: dict[str, Any] = {}
    browser_launch_attempted = False
    cdp_connection_attempted = False
    try:
        browser_launch_attempted = True
        launch_info = dict(launcher.launch() or {})
        endpoint = str(launch_info.get("cdp_endpoint") or "http://127.0.0.1")
        cdp_connection_attempted = True
        cdp_client.connect(endpoint)
        cdp_client.navigate(target_url)
        state = dict(cdp_client.read_state() or {})
        screenshot_bytes = bytes(cdp_client.capture_screenshot() or b"")
    finally:
        close_client = getattr(cdp_client, "close", None)
        if callable(close_client):
            close_client()
        close_launcher = getattr(launcher, "close", None)
        if callable(close_launcher):
            close_launcher()

    safe_id = gate_approval_id.replace(".", "-")
    root = Path(vault_root)
    browser_dir = root / "07_LOGS" / "Browser-Runs"
    screenshot_dir = root / "07_LOGS" / "Operator-Screenshots"
    activity_dir = root / "07_LOGS" / "Agent-Activity"
    candidate_dir = root / "03_INPUTS" / "Browser-Skill-Candidates" / _domain_slug(_allowed_domains_for_target(target_url)[0])
    for directory in (browser_dir, screenshot_dir, activity_dir, candidate_dir):
        directory.mkdir(parents=True, exist_ok=True)
    screenshot_path = screenshot_dir / f"cdp-read-only-proof-{safe_id}.png"
    dom_path = browser_dir / f"cdp-read-only-proof-{safe_id}-dom.json"
    run_path = browser_dir / f"cdp-read-only-proof-{safe_id}.json"
    activity_path = activity_dir / f"cdp-read-only-proof-{safe_id}.md"
    candidate_path = candidate_dir / f"cdp-read-only-proof-{safe_id}.md"
    screenshot_path.write_bytes(screenshot_bytes)
    dom_path.write_text(json.dumps(state.get("dom_snapshot") or {}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    result = {
        "ok": True,
        "status": "implemented_cdp_read_only_proof_complete",
        "executor_status": "implemented",
        "execution_enabled": True,
        "cdp_read_only_proof_allowed": True,
        "operation": BROWSER_CDP_READ_ONLY_PROOF_OPERATION,
        "approval_schema_id": BROWSER_CDP_READ_ONLY_PROOF_APPROVAL_SCHEMA_ID,
        "gate_approval_id": gate_approval_id,
        "approval_consumed": True,
        "consumption_ref": consumption.get("consumption_ref"),
        "approval_decision_written": False,
        "idempotency_marker_written": True,
        "idempotency_marker_ref": marker.get("marker_ref"),
        "browser_launch_attempted": browser_launch_attempted,
        "cdp_connection_attempted": cdp_connection_attempted,
        "screenshot_attempted": True,
        "dom_snapshot_attempted": True,
        "credential_value_read": False,
        "cookie_or_session_read": False,
        "real_profile_used": False,
        "trusted_skill_written": False,
        "canonical_files_mutated": False,
        "agent_bus_task_enqueued": False,
        "provider_call_attempted": False,
        "files_modified": True,
        "runtime": runtime,
        "target_url": target_url,
        "title": state.get("title"),
        "url": state.get("url"),
        "visible_text_preview": str(state.get("visible_text") or "")[:500],
        "screenshot_path": str(screenshot_path),
        "dom_snapshot_path": str(dom_path),
        "browser_run_log_path": str(run_path),
        "agent_activity_log_path": str(activity_path),
        "skill_candidate_path": str(candidate_path),
        "source_command": source_command,
    }
    run_path.write_text(json.dumps({"record_type": "browser_cdp_read_only_proof_run", "result": result}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    activity_path.write_text(
        "\n".join([
            "---",
            f"runtime: {runtime}",
            "activity_type: browser-cdp-read-only-proof",
            "status: complete",
            "---",
            "",
            f"# Browser CDP Read-Only Proof - {gate_approval_id}",
            "",
            f"- Target URL: `{target_url}`",
            f"- Browser run log: `{run_path}`",
            f"- Screenshot: `{screenshot_path}`",
            f"- DOM snapshot: `{dom_path}`",
            "- Credentials/cookies/sessions/real profile: not read",
            "- Trusted skill/canonical writeback: not performed",
        ]) + "\n",
        encoding="utf-8",
    )
    candidate_path.write_text(
        f"# Untrusted Browser CDP Proof Candidate - {gate_approval_id}\n\n"
        f"- Target URL: `{target_url}`\n"
        f"- Title: `{state.get('title')}`\n"
        f"- Screenshot artifact: `{screenshot_path}`\n"
        f"- DOM artifact: `{dom_path}`\n"
        "- Trust tier: Tier 4 untrusted evidence; not activated.\n",
        encoding="utf-8",
    )
    marker_record = json.loads(Path(marker["marker_ref"]).read_text(encoding="utf-8"))
    marker_record.update({
        "status": "completed",
        "completed_at": _utc_now(),
        "browser_launch_attempted": True,
        "cdp_connection_attempted": True,
        "screenshot_attempted": True,
        "dom_snapshot_attempted": True,
        "browser_run_log_path": str(run_path),
    })
    Path(marker["marker_ref"]).write_text(json.dumps(marker_record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def build_cdp_read_only_executor_dry_run_plan(
    vault_root: str | Path,
    gate_approval_id: str,
    *,
    target_url: str | None = None,
    cdp_endpoint: str | None = None,
    runtime: str = "unknown",
    source_command: str | None = None,
) -> dict[str, Any]:
    """Return the future CDP executor plan without consuming approval or executing."""
    _validate_gate_approval_id(gate_approval_id)
    reservation = build_cdp_read_only_idempotency_reservation_spec(
        vault_root,
        gate_approval_id,
        target_url=target_url,
        cdp_endpoint=cdp_endpoint,
        runtime=runtime,
        source_command=source_command or "chaseos runtime browser-cdp executor-dry-run",
    )
    idempotency = reservation.get("idempotency") if isinstance(reservation.get("idempotency"), dict) else {}
    marker_path = str(idempotency.get("marker_path") or cdp_read_only_idempotency_marker_path(vault_root, gate_approval_id))
    future_write_plan = (
        (reservation.get("marker_record_template") or {}).get("future_write_plan")
        if isinstance(reservation.get("marker_record_template"), dict)
        else {}
    )
    target_writes = list(future_write_plan.get("targets") or []) if isinstance(future_write_plan, dict) else []
    reservation_status = str(reservation.get("reservation_status") or "unknown")
    validation = reservation.get("approval_validation") if isinstance(reservation.get("approval_validation"), dict) else {}
    approval_status = str(reservation.get("approval_status") or "missing")
    structurally_valid = bool(validation.get("structurally_valid"))
    matches_preflight = bool(validation.get("matches_preflight"))
    marker_exists = bool(idempotency.get("marker_exists"))
    write_plan_limited = _future_write_plan_is_limited(future_write_plan)

    if reservation_status.startswith("blocked_"):
        dry_run_status = reservation_status
        next_action = str(reservation.get("next_action") or "resolve_reservation_blocker_before_executor")
    else:
        dry_run_status = "blocked_executor_not_built"
        next_action = "implement_executor_only_after_approval_consumption_and_marker_writer_policy"

    future_execution_sequence = [
        {
            "step_id": "reload_and_validate_approval_artifact",
            "future_action": "re-read approval artifact and verify digest/status immediately before execution",
            "implemented": True,
            "attempted_now": False,
            "required_before_browser_action": True,
        },
        {
            "step_id": "consume_approval_decision",
            "future_action": "immutably consume an approved Gate decision for this one CDP proof",
            "implemented": False,
            "attempted_now": False,
            "required_before_browser_action": True,
        },
        {
            "step_id": "reserve_idempotency_marker",
            "future_action": "atomically create the single-use idempotency marker",
            "implemented": False,
            "attempted_now": False,
            "required_before_browser_action": True,
            "target_path": marker_path,
        },
        {
            "step_id": "launch_isolated_browser",
            "future_action": "launch a ChaseOS-created throwaway local browser context",
            "implemented": False,
            "attempted_now": False,
            "required_before_cdp_connection": True,
        },
        {
            "step_id": "connect_local_cdp",
            "future_action": "connect only to a local 127.0.0.1, localhost, or ::1 CDP endpoint",
            "implemented": False,
            "attempted_now": False,
        },
        {
            "step_id": "navigate_and_observe",
            "future_action": "navigate to the approved target URL and read title/url/visible text",
            "implemented": False,
            "attempted_now": False,
        },
        {
            "step_id": "capture_bounded_evidence",
            "future_action": "capture screenshot and DOM snapshot only if redaction/retention rules pass",
            "implemented": False,
            "attempted_now": False,
        },
        {
            "step_id": "write_declared_artifacts",
            "future_action": "write only declared Browser Run, Agent Activity, screenshot, and untrusted candidate artifacts",
            "implemented": False,
            "attempted_now": False,
            "target_writes": target_writes,
        },
        {
            "step_id": "close_context_and_record_result",
            "future_action": "close the isolated browser context and write success/failure evidence without deleting the marker",
            "implemented": False,
            "attempted_now": False,
        },
    ]

    return {
        "ok": True,
        "schema_version": 1,
        "operation": BROWSER_CDP_READ_ONLY_PROOF_OPERATION,
        "approval_schema_id": BROWSER_CDP_READ_ONLY_PROOF_APPROVAL_SCHEMA_ID,
        "gate_approval_id": gate_approval_id,
        "dry_run_status": dry_run_status,
        "dry_run_only": True,
        "executor_status": "implemented",
        "execution_enabled": approval_status == "approved" and structurally_valid and matches_preflight and not marker_exists and write_plan_limited,
        "cdp_read_only_proof_allowed": approval_status == "approved" and structurally_valid and matches_preflight and not marker_exists and write_plan_limited,
        "approval_status": reservation.get("approval_status"),
        "approval_status_approved": reservation.get("approval_status_approved"),
        "approval_decision_accepted": False,
        "reservation_spec": reservation,
        "idempotency": {
            "marker_path": marker_path,
            "marker_exists": bool(idempotency.get("marker_exists")),
            "idempotency_marker_written": False,
            "future_marker_write_mode": "atomic_create_new_only",
        },
        "future_execution_sequence": future_execution_sequence,
        "future_artifacts": {
            "marker_path": marker_path,
            "write_plan": future_write_plan,
            "writes_attempted": False,
        },
        "stop_conditions": [
            "approval artifact missing, invalid, mismatched, expired, revoked, denied, or not approved",
            "approval decision cannot be immutably consumed",
            "idempotency marker already exists or cannot be created atomically",
            "target URL or CDP endpoint is not local/allowlisted",
            "isolated browser launch would use an existing real profile",
            "requested action would read credentials, cookies, sessions, storage, or browser history",
            "requested artifact target leaves Browser Run, Agent Activity, Operator Screenshots, or untrusted candidates",
            "page is authenticated, private, sensitive, or requires credential entry",
            "screenshot or DOM evidence would expose sensitive data and cannot be redacted",
        ],
        "feature_completion_tracker": {
            "pre_execution_governance_status": "complete_after_dry_run_plan_targeted_verification",
            "live_cdp_execution_status": "not_built",
            "remaining_live_requirements": [
                "real_isolated_browser_launcher",
                "isolated_browser_launcher",
                "local_cdp_client",
                "default_cli_live_client_binding",
                "failure_evidence_and_retry_policy",
            ],
        },
        "blocked_reasons": list(dict.fromkeys(reservation.get("blocked_reasons") or [])),
        "approval_consumed": False,
        "approval_artifact_mutated": False,
        "approval_request_written": False,
        "idempotency_marker_written": False,
        "browser_launch_attempted": False,
        "cdp_connection_attempted": False,
        "screenshot_attempted": False,
        "dom_snapshot_attempted": False,
        "credential_value_read": False,
        "cookie_or_session_read": False,
        "real_profile_used": False,
        "trusted_skill_written": False,
        "canonical_files_mutated": False,
        "agent_bus_task_enqueued": False,
        "provider_call_attempted": False,
        "files_modified": False,
        "next_action": next_action,
        "source_command": source_command,
    }


def build_cdp_read_only_approval_decision_policy(
    vault_root: str | Path,
    gate_approval_id: str,
    *,
    target_url: str | None = None,
    cdp_endpoint: str | None = None,
    runtime: str = "unknown",
    source_command: str | None = None,
) -> dict[str, Any]:
    """Return the future approval-decision consumption policy without consuming approval."""
    _validate_gate_approval_id(gate_approval_id)
    dry_run = build_cdp_read_only_executor_dry_run_plan(
        vault_root,
        gate_approval_id,
        target_url=target_url,
        cdp_endpoint=cdp_endpoint,
        runtime=runtime,
        source_command=source_command or "chaseos runtime browser-cdp approval-decision-policy",
    )
    reservation = dry_run.get("reservation_spec") if isinstance(dry_run.get("reservation_spec"), dict) else {}
    validation = (
        reservation.get("approval_validation")
        if isinstance(reservation.get("approval_validation"), dict)
        else {}
    )
    approval_status = str(dry_run.get("approval_status") or "missing")
    structurally_valid = bool(validation.get("structurally_valid"))
    request_digest = validation.get("request_digest_sha256")
    approved_metadata_present = approval_status == "approved" and bool(validation.get("approved_by")) and bool(
        validation.get("approved_at")
    )

    if not structurally_valid:
        policy_status = "blocked_approval_artifact_invalid"
        next_action = "operator_must_recreate_or_fix_browser_cdp_approval_artifact"
    elif approval_status != "approved":
        policy_status = "blocked_approval_not_approved"
        next_action = "operator_or_gate_must_record_an_approved_decision_before_future_consumption"
    elif not approved_metadata_present:
        policy_status = "blocked_approval_decision_metadata_missing"
        next_action = "operator_or_gate_must_bind_approved_by_and_approved_at_before_future_consumption"
    else:
        policy_status = "approved_artifact_policy_ready_but_consumer_not_built"
        next_action = "implement_immutable_decision_consumer_before_any_marker_or_browser_action"

    decision_record_template = {
        "record_type": "browser_cdp_read_only_proof_approval_decision",
        "schema_version": 1,
        "operation": BROWSER_CDP_READ_ONLY_PROOF_OPERATION,
        "approval_schema_id": BROWSER_CDP_READ_ONLY_PROOF_APPROVAL_SCHEMA_ID,
        "gate_approval_id": gate_approval_id,
        "decision_id": "<future-gate-decision-id>",
        "decision_status": "approved|denied|revoked|expired",
        "decided_by": "<future-operator-or-gate-identity>",
        "decided_at": "<future-runtime-utc>",
        "expires_at": "<future-runtime-utc-or-null>",
        "source_approval_artifact_ref": validation.get("artifact_ref"),
        "source_approval_request_digest_sha256": request_digest,
        "target_url": str(target_url or ""),
        "runtime": runtime,
        "single_use": True,
        "approval_consumed": False,
        "consumed_at": None,
        "consumed_by": None,
        "idempotency_marker_path": (dry_run.get("idempotency") or {}).get("marker_path"),
        "allowed_effect": "one_future_local_read_only_cdp_proof_after_marker_reservation",
        "forbidden_effects": [
            "credential_or_cookie_or_session_access",
            "real_profile_use",
            "raw_cdp_passthrough",
            "trusted_skill_write",
            "canonical_writeback",
            "agent_bus_enqueue",
            "provider_call",
        ],
        "decision_digest_sha256": "<future-decision-digest>",
    }

    return {
        "ok": True,
        "schema_version": 1,
        "operation": BROWSER_CDP_READ_ONLY_PROOF_OPERATION,
        "approval_schema_id": BROWSER_CDP_READ_ONLY_PROOF_APPROVAL_SCHEMA_ID,
        "gate_approval_id": gate_approval_id,
        "policy_status": policy_status,
        "approval_status": approval_status,
        "approval_artifact_structurally_valid": structurally_valid,
        "approval_decision_metadata_present": approved_metadata_present,
        "approval_decision_accepted": False,
        "approval_consumption_policy": {
            "consumer_status": "not_built",
            "approved_status_alone_is_sufficient": False,
            "requires_structural_validation": True,
            "requires_request_digest_match": True,
            "requires_decision_identity": True,
            "requires_decision_timestamp": True,
            "requires_expiry_check": True,
            "requires_single_use_consumption": True,
            "requires_idempotency_marker_absent_before_consumption": True,
            "requires_marker_write_after_consumption_before_browser_action": True,
        },
        "decision_record_template": decision_record_template,
        "decision_consume_rules": [
            "re-read and validate the approval artifact immediately before consumption",
            "reject approved status without approved_by and approved_at metadata",
            "bind the decision to operation, gate_approval_id, target_url, runtime, and request digest",
            "reject expired, revoked, denied, mismatched, or already-consumed decisions",
            "consume at most once and write an immutable consumption event before marker creation",
            "do not launch browser or connect CDP until decision consumption and marker reservation both pass",
            "do not store credentials, cookies, session tokens, browser storage, or profile paths in the decision record",
        ],
        "dry_run_plan": dry_run,
        "blocked_reasons": list(dict.fromkeys(dry_run.get("blocked_reasons") or [])),
        "approval_consumed": False,
        "approval_artifact_mutated": False,
        "approval_request_written": False,
        "approval_decision_written": False,
        "idempotency_marker_written": False,
        "browser_launch_attempted": False,
        "cdp_connection_attempted": False,
        "screenshot_attempted": False,
        "dom_snapshot_attempted": False,
        "credential_value_read": False,
        "cookie_or_session_read": False,
        "real_profile_used": False,
        "trusted_skill_written": False,
        "canonical_files_mutated": False,
        "agent_bus_task_enqueued": False,
        "provider_call_attempted": False,
        "files_modified": False,
        "next_action": next_action,
        "source_command": source_command,
    }


def build_cdp_read_only_approval_decision_consumer_design(
    vault_root: str | Path,
    gate_approval_id: str,
    *,
    target_url: str | None = None,
    cdp_endpoint: str | None = None,
    runtime: str = "unknown",
    source_command: str | None = None,
) -> dict[str, Any]:
    """Return the future approval decision consumer design without consuming approval."""
    _validate_gate_approval_id(gate_approval_id)
    decision_policy = build_cdp_read_only_approval_decision_policy(
        vault_root,
        gate_approval_id,
        target_url=target_url,
        cdp_endpoint=cdp_endpoint,
        runtime=runtime,
        source_command=source_command or "chaseos runtime browser-cdp approval-decision-consumer-design",
    )
    dry_run = (
        decision_policy.get("dry_run_plan")
        if isinstance(decision_policy.get("dry_run_plan"), dict)
        else {}
    )
    reservation = (
        dry_run.get("reservation_spec")
        if isinstance(dry_run.get("reservation_spec"), dict)
        else {}
    )
    validation = (
        reservation.get("approval_validation")
        if isinstance(reservation.get("approval_validation"), dict)
        else {}
    )
    idempotency = dry_run.get("idempotency") if isinstance(dry_run.get("idempotency"), dict) else {}
    marker_path = cdp_read_only_idempotency_marker_path(vault_root, gate_approval_id)
    marker_exists = bool(idempotency.get("marker_exists") or marker_path.exists())
    approval_status = str(decision_policy.get("approval_status") or "missing")
    policy_status = str(decision_policy.get("policy_status") or "unknown")
    structurally_valid = bool(decision_policy.get("approval_artifact_structurally_valid"))
    decision_metadata_present = bool(decision_policy.get("approval_decision_metadata_present"))
    request_digest = validation.get("request_digest_sha256")

    if not structurally_valid:
        consumer_design_status = "blocked_approval_artifact_invalid"
        next_action = "operator_must_recreate_or_fix_browser_cdp_approval_artifact"
    elif marker_exists:
        consumer_design_status = "blocked_prior_cdp_proof_marker_exists"
        next_action = "operator_must_review_existing_marker_before_any_decision_consumer"
    elif approval_status != "approved":
        consumer_design_status = "blocked_approval_not_approved"
        next_action = "operator_or_gate_must_record_an_approved_decision_before_future_consumption"
    elif not decision_metadata_present:
        consumer_design_status = "blocked_approval_decision_metadata_missing"
        next_action = "operator_or_gate_must_bind_approved_by_and_approved_at_before_future_consumption"
    elif policy_status != "approved_artifact_policy_ready_but_consumer_not_built":
        consumer_design_status = "blocked_decision_policy_not_ready"
        next_action = "resolve_decision_policy_blocker_before_consumer_implementation"
    else:
        consumer_design_status = "ready_for_future_approval_decision_consumer_but_consumer_not_built"
        next_action = "implement_decision_consumer_only_before_marker_writer_and_browser_actions"

    consume_record_template = dict(decision_policy.get("decision_record_template") or {})
    consume_record_template.update(
        {
            "consumer_record_schema": "browser_cdp_read_only_approval_decision_consumer.v1",
            "consumer_status": "future_single_use_consumed_before_marker_write",
            "source_request_digest_sha256": request_digest,
            "consumption_digest_sha256": "<future-consumption-digest>",
            "consumer_side_effects": {
                "approval_artifact_mutated": False,
                "approval_decision_written_now": False,
                "approval_consumed_now": False,
                "idempotency_marker_written_now": False,
                "browser_launch_attempted_before_consumption": False,
                "cdp_connection_attempted_before_consumption": False,
            },
        }
    )

    return {
        "ok": True,
        "schema_version": 1,
        "operation": BROWSER_CDP_READ_ONLY_PROOF_OPERATION,
        "approval_schema_id": BROWSER_CDP_READ_ONLY_PROOF_APPROVAL_SCHEMA_ID,
        "gate_approval_id": gate_approval_id,
        "consumer_design_status": consumer_design_status,
        "consumer_status": "not_built",
        "execution_enabled": False,
        "cdp_read_only_proof_allowed": False,
        "approval_status": approval_status,
        "approval_status_approved": approval_status == "approved",
        "approval_decision_accepted": False,
        "approval_decision_policy": decision_policy,
        "approval_validation": validation,
        "idempotency": {
            "marker_path": str(marker_path),
            "marker_exists": marker_exists,
            "idempotency_marker_written": False,
            "future_marker_write_required_after_consumption": True,
        },
        "consume_record_template": consume_record_template,
        "consumer_algorithm": [
            "re-read approval artifact and decision metadata immediately before consumption",
            "verify operation, schema id, gate_approval_id, target URL, runtime, request digest, and approval identity",
            "reject pending, denied, revoked, expired, mismatched, duplicate, or already-consumed decisions",
            "reject if an idempotency marker already exists before consumption",
            "record a future immutable consumption event before any marker write",
            "do not mutate the source approval artifact while consuming the decision",
            "do not write marker, launch browser, connect CDP, or capture proof artifacts during consumption design",
        ],
        "single_use_constraints": {
            "single_use_required": True,
            "source_approval_mutation_allowed": False,
            "decision_overwrite_allowed": False,
            "consume_twice_allowed": False,
            "marker_must_be_absent_before_consumption": True,
            "marker_write_required_after_consumption_before_browser_action": True,
        },
        "future_consumer_preconditions": [
            _precondition(
                "approval_artifact_structurally_valid",
                passed=structurally_valid,
                status="passed" if structurally_valid else "blocked",
                reason=str(validation.get("reason") or "approval artifact validation failed"),
            ),
            _precondition(
                "approval_status_approved",
                passed=approval_status == "approved",
                status=approval_status,
                reason="approval artifact must be approved before the decision consumer can run",
            ),
            _precondition(
                "approval_decision_metadata_present",
                passed=decision_metadata_present,
                status="passed" if decision_metadata_present else "blocked",
                reason="approved_by and approved_at must be present before future consumption",
            ),
            _precondition(
                "idempotency_marker_absent",
                passed=not marker_exists,
                status="absent" if not marker_exists else "present",
                reason="decision consumer must fail if a marker already exists",
                evidence={"marker_path": str(marker_path)},
            ),
            _precondition(
                "approval_decision_consumer_built",
                passed=False,
                status="not_built",
                reason="approval decision consumer implementation is not built",
            ),
        ],
        "forbidden_consumer_fields": [
            "password",
            "api_key",
            "authorization",
            "cookie",
            "session",
            "local_storage",
            "indexed_db",
            "user_data_dir",
            "profile_path",
            "browser_history",
        ],
        "blocked_reasons": list(dict.fromkeys(decision_policy.get("blocked_reasons") or [])),
        "approval_consumed": False,
        "approval_artifact_mutated": False,
        "approval_request_written": False,
        "approval_decision_written": False,
        "idempotency_marker_written": False,
        "browser_launch_attempted": False,
        "cdp_connection_attempted": False,
        "screenshot_attempted": False,
        "dom_snapshot_attempted": False,
        "credential_value_read": False,
        "cookie_or_session_read": False,
        "real_profile_used": False,
        "trusted_skill_written": False,
        "canonical_files_mutated": False,
        "agent_bus_task_enqueued": False,
        "provider_call_attempted": False,
        "files_modified": False,
        "next_action": next_action,
        "source_command": source_command,
    }


def build_cdp_read_only_atomic_marker_writer_design(
    vault_root: str | Path,
    gate_approval_id: str,
    *,
    target_url: str | None = None,
    cdp_endpoint: str | None = None,
    runtime: str = "unknown",
    source_command: str | None = None,
) -> dict[str, Any]:
    """Return the future atomic marker writer design without writing a marker."""
    _validate_gate_approval_id(gate_approval_id)
    decision_policy = build_cdp_read_only_approval_decision_policy(
        vault_root,
        gate_approval_id,
        target_url=target_url,
        cdp_endpoint=cdp_endpoint,
        runtime=runtime,
        source_command=source_command or "chaseos runtime browser-cdp atomic-marker-writer-design",
    )
    dry_run = (
        decision_policy.get("dry_run_plan")
        if isinstance(decision_policy.get("dry_run_plan"), dict)
        else {}
    )
    reservation = (
        dry_run.get("reservation_spec")
        if isinstance(dry_run.get("reservation_spec"), dict)
        else {}
    )
    validation = (
        reservation.get("approval_validation")
        if isinstance(reservation.get("approval_validation"), dict)
        else {}
    )
    idempotency = (
        reservation.get("idempotency")
        if isinstance(reservation.get("idempotency"), dict)
        else {}
    )
    marker_path = cdp_read_only_idempotency_marker_path(vault_root, gate_approval_id)
    marker_exists = bool(idempotency.get("marker_exists") or marker_path.exists())
    approval_status = str(decision_policy.get("approval_status") or "missing")
    policy_status = str(decision_policy.get("policy_status") or "unknown")
    structurally_valid = bool(decision_policy.get("approval_artifact_structurally_valid"))
    decision_metadata_present = bool(decision_policy.get("approval_decision_metadata_present"))

    if not structurally_valid:
        writer_status = "blocked_approval_artifact_invalid"
        next_action = "operator_must_recreate_or_fix_browser_cdp_approval_artifact"
    elif marker_exists:
        writer_status = "blocked_prior_cdp_proof_marker_exists"
        next_action = "operator_must_review_existing_marker_before_any_writer_implementation"
    elif approval_status != "approved":
        writer_status = "blocked_approval_not_approved"
        next_action = "operator_or_gate_must_record_an_approved_decision_before_marker_writer"
    elif not decision_metadata_present:
        writer_status = "blocked_approval_decision_metadata_missing"
        next_action = "operator_or_gate_must_bind_approved_by_and_approved_at_before_marker_writer"
    elif policy_status != "approved_artifact_policy_ready_but_consumer_not_built":
        writer_status = "blocked_decision_policy_not_ready"
        next_action = "resolve_decision_policy_blocker_before_marker_writer"
    else:
        writer_status = "ready_for_future_atomic_marker_writer_but_writer_not_built"
        next_action = "implement_marker_writer_only_after_decision_consumer_is_built_and_verified"

    marker_record_template = dict(reservation.get("marker_record_template") or {})
    marker_record_template.update(
        {
            "writer_record_schema": "browser_cdp_read_only_atomic_marker_writer.v1",
            "writer_status": "future_reserved_by_atomic_create_new_only",
            "approval_decision_policy_status": policy_status,
            "approval_decision_digest_sha256": "<future-approved-decision-digest>",
            "marker_payload_digest_sha256": "<future-marker-payload-digest>",
            "writer_side_effects": {
                "approval_consumed_before_write": True,
                "browser_launch_attempted_before_write": False,
                "cdp_connection_attempted_before_write": False,
                "idempotency_marker_written_now": False,
            },
        }
    )

    return {
        "ok": True,
        "schema_version": 1,
        "operation": BROWSER_CDP_READ_ONLY_PROOF_OPERATION,
        "approval_schema_id": BROWSER_CDP_READ_ONLY_PROOF_APPROVAL_SCHEMA_ID,
        "gate_approval_id": gate_approval_id,
        "writer_design_status": writer_status,
        "writer_status": "not_built",
        "execution_enabled": False,
        "cdp_read_only_proof_allowed": False,
        "approval_status": approval_status,
        "approval_status_approved": approval_status == "approved",
        "approval_decision_accepted": False,
        "approval_decision_policy": decision_policy,
        "approval_validation": validation,
        "idempotency": {
            "marker_path": str(marker_path),
            "marker_exists": marker_exists,
            "idempotency_marker_written": False,
            "future_marker_write_mode": "atomic_create_new_only",
        },
        "marker_record_template": marker_record_template,
        "atomic_write_algorithm": [
            "re-read approval artifact and immutable approval decision immediately before marker write",
            "verify request digest, target URL, runtime, approval schema, decision identity, and expiry",
            "resolve marker path under the ChaseOS CDP marker directory and reject path escape",
            "create parent marker directory if absent without touching other directories",
            "open marker path with create-new/exclusive semantics; fail if it already exists",
            "write only the sanitized marker JSON payload and flush it before any browser action",
            "on any later proof failure, write failure evidence to declared log surfaces and keep the marker",
        ],
        "path_constraints": {
            "marker_directory": str((Path(vault_root) / IDEMPOTENCY_MARKER_RELATIVE_DIR).resolve()),
            "marker_path": str(marker_path),
            "path_escape_allowed": False,
            "overwrite_allowed": False,
            "delete_on_failure_allowed": False,
            "retry_without_new_approval_allowed": False,
        },
        "future_writer_preconditions": [
            _precondition(
                "approval_artifact_structurally_valid",
                passed=structurally_valid,
                status="passed" if structurally_valid else "blocked",
                reason=str(validation.get("reason") or "approval artifact validation failed"),
            ),
            _precondition(
                "approval_status_approved",
                passed=approval_status == "approved",
                status=approval_status,
                reason="approval artifact must be approved before marker writer can run",
            ),
            _precondition(
                "approval_decision_metadata_present",
                passed=decision_metadata_present,
                status="passed" if decision_metadata_present else "blocked",
                reason="approved_by and approved_at must be present before future consumption",
            ),
            _precondition(
                "approval_decision_consumer_built",
                passed=False,
                status="not_built",
                reason="marker writer depends on immutable decision consumption",
            ),
            _precondition(
                "idempotency_marker_absent",
                passed=not marker_exists,
                status="absent" if not marker_exists else "present",
                reason="future writer must fail if a marker already exists",
                evidence={"marker_path": str(marker_path)},
            ),
            _precondition(
                "atomic_marker_writer_built",
                passed=False,
                status="not_built",
                reason="atomic marker writer implementation is not built",
            ),
        ],
        "failure_handling_policy": [
            "do not delete the marker after partial or failed proof execution",
            "do not retry with the same gate_approval_id after marker creation",
            "write failure evidence only to Browser Run and Agent Activity surfaces",
            "require operator review and a new approval request before any retry",
        ],
        "forbidden_marker_fields": [
            "password",
            "api_key",
            "authorization",
            "cookie",
            "session",
            "local_storage",
            "indexed_db",
            "user_data_dir",
            "profile_path",
            "browser_history",
        ],
        "blocked_reasons": list(dict.fromkeys(decision_policy.get("blocked_reasons") or [])),
        "approval_consumed": False,
        "approval_artifact_mutated": False,
        "approval_request_written": False,
        "approval_decision_written": False,
        "idempotency_marker_written": False,
        "marker_directory_created": False,
        "browser_launch_attempted": False,
        "cdp_connection_attempted": False,
        "screenshot_attempted": False,
        "dom_snapshot_attempted": False,
        "credential_value_read": False,
        "cookie_or_session_read": False,
        "real_profile_used": False,
        "trusted_skill_written": False,
        "canonical_files_mutated": False,
        "agent_bus_task_enqueued": False,
        "provider_call_attempted": False,
        "files_modified": False,
        "next_action": next_action,
        "source_command": source_command,
    }


def build_cdp_read_only_isolated_browser_launcher_design(
    vault_root: str | Path,
    gate_approval_id: str,
    *,
    target_url: str | None = None,
    cdp_endpoint: str | None = None,
    runtime: str = "unknown",
    source_command: str | None = None,
) -> dict[str, Any]:
    """Return the future isolated browser launcher contract without launching a browser."""
    _validate_gate_approval_id(gate_approval_id)
    marker_design = build_cdp_read_only_atomic_marker_writer_design(
        vault_root,
        gate_approval_id,
        target_url=target_url,
        cdp_endpoint=cdp_endpoint,
        runtime=runtime,
        source_command=source_command or "chaseos runtime browser-cdp isolated-browser-launcher-design",
    )
    validation = marker_design.get("approval_validation") if isinstance(marker_design.get("approval_validation"), dict) else {}
    idempotency = marker_design.get("idempotency") if isinstance(marker_design.get("idempotency"), dict) else {}
    marker_exists = bool(idempotency.get("marker_exists"))
    approval_status = str(marker_design.get("approval_status") or "missing")
    writer_design_status = str(marker_design.get("writer_design_status") or "unknown")
    structurally_valid = bool(validation.get("structurally_valid"))
    target = target_url or DEFAULT_LOCAL_TARGET_URL
    endpoint = cdp_endpoint or DEFAULT_LOCAL_CDP_ENDPOINT

    if not structurally_valid:
        launcher_design_status = "blocked_approval_artifact_invalid"
        next_action = "operator_must_recreate_or_fix_browser_cdp_approval_artifact"
    elif marker_exists:
        launcher_design_status = "blocked_prior_cdp_proof_marker_exists"
        next_action = "operator_must_review_existing_marker_before_launcher_implementation"
    elif approval_status != "approved":
        launcher_design_status = "blocked_approval_not_approved"
        next_action = "operator_or_gate_must_record_an_approved_decision_before_launcher"
    elif writer_design_status != "ready_for_future_atomic_marker_writer_but_writer_not_built":
        launcher_design_status = "blocked_marker_writer_design_not_ready"
        next_action = "resolve_marker_writer_design_blocker_before_launcher"
    else:
        launcher_design_status = "ready_for_future_isolated_launcher_but_launcher_not_built"
        next_action = "implement_real_launcher_only_after_marker_writer_and_local_cdp_client_boundaries_are_verified"

    return {
        "ok": True,
        "schema_version": 1,
        "operation": BROWSER_CDP_READ_ONLY_PROOF_OPERATION,
        "approval_schema_id": BROWSER_CDP_READ_ONLY_PROOF_APPROVAL_SCHEMA_ID,
        "gate_approval_id": gate_approval_id,
        "launcher_design_status": launcher_design_status,
        "launcher_status": "not_built",
        "execution_enabled": False,
        "cdp_read_only_proof_allowed": False,
        "approval_status": approval_status,
        "approval_status_approved": approval_status == "approved",
        "approval_validation": validation,
        "atomic_marker_writer_design": marker_design,
        "target_url": target,
        "cdp_endpoint": endpoint,
        "launch_strategy": "chaseos_launch_isolated",
        "browser_profile_policy": "throwaway_only",
        "launcher_contract": {
            "launcher_kind": "future_chaseos_owned_local_chromium_launcher",
            "allowed_hosts": ["127.0.0.1", "localhost", "::1"],
            "debugging_address": "127.0.0.1",
            "debugging_port_policy": "allocate_unused_local_port_per_run",
            "profile_strategy": "new_throwaway_user_data_dir_per_run",
            "profile_path_logging": "opaque_launcher_temp_ref_only",
            "browser_executable_policy": "operator_configured_or_chaseos_managed_path_only",
            "attach_to_existing_browser_allowed": False,
            "real_profile_allowed": False,
            "persistent_profile_allowed": False,
            "public_debugging_endpoint_allowed": False,
        },
        "required_launch_arguments": [
            "--remote-debugging-address=127.0.0.1",
            "--remote-debugging-port=<future-allocated-local-port>",
            "--user-data-dir=<future-throwaway-profile-ref>",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-sync",
        ],
        "forbidden_launch_arguments": [
            "--profile-directory",
            "--load-extension",
            "--remote-debugging-address=0.0.0.0",
            "--remote-debugging-address=<public-host>",
            "--user-data-dir=<operator-real-profile>",
        ],
        "launcher_sequence": [
            "verify approval consumption and idempotency marker are complete before launch",
            "allocate a local-only CDP port bound to 127.0.0.1",
            "create an isolated throwaway profile directory without logging its raw absolute path",
            "spawn only the configured Chrome/Chromium executable with the approved argument set",
            "wait for local CDP readiness with timeout",
            "hand only the local endpoint to the bounded CDP client",
            "close the browser context and remove throwaway profile state after proof completion",
        ],
        "future_launcher_preconditions": [
            _precondition(
                "approval_artifact_structurally_valid",
                passed=structurally_valid,
                status="passed" if structurally_valid else "blocked",
                reason=str(validation.get("reason") or "approval artifact validation failed"),
            ),
            _precondition(
                "approval_status_approved",
                passed=approval_status == "approved",
                status=approval_status,
                reason="approval must be approved before a launcher can be used",
            ),
            _precondition(
                "idempotency_marker_absent_before_design",
                passed=not marker_exists,
                status="absent" if not marker_exists else "present",
                reason="launcher design must flag already-used approvals before any process launch",
            ),
            _precondition(
                "atomic_marker_writer_ready",
                passed=writer_design_status == "ready_for_future_atomic_marker_writer_but_writer_not_built",
                status=writer_design_status,
                reason="future launcher must run only after marker writer boundaries are satisfied",
            ),
            _precondition(
                "isolated_browser_launcher_built",
                passed=False,
                status="not_built",
                reason="real isolated browser launcher implementation is not built",
            ),
        ],
        "cleanup_policy": [
            "close browser process even if CDP proof fails",
            "remove throwaway profile directory after close unless failure evidence requires a redacted reference",
            "never copy cookies, sessions, history, local storage, extensions, or profile state into ChaseOS logs",
            "write launch failures only to Browser Run and Agent Activity evidence surfaces",
        ],
        "forbidden_launcher_fields": [
            "password",
            "api_key",
            "authorization",
            "cookie",
            "session",
            "local_storage",
            "indexed_db",
            "user_data_dir",
            "profile_path",
            "browser_history",
            "extension_state",
        ],
        "blocked_reasons": list(dict.fromkeys(marker_design.get("blocked_reasons") or [])),
        "approval_consumed": False,
        "approval_artifact_mutated": False,
        "approval_request_written": False,
        "approval_decision_written": False,
        "idempotency_marker_written": False,
        "marker_directory_created": False,
        "browser_launch_attempted": False,
        "browser_process_spawned": False,
        "throwaway_profile_created": False,
        "cdp_port_opened": False,
        "cdp_connection_attempted": False,
        "screenshot_attempted": False,
        "dom_snapshot_attempted": False,
        "credential_value_read": False,
        "cookie_or_session_read": False,
        "real_profile_used": False,
        "trusted_skill_written": False,
        "canonical_files_mutated": False,
        "agent_bus_task_enqueued": False,
        "provider_call_attempted": False,
        "files_modified": False,
        "next_action": next_action,
        "source_command": source_command,
    }


def build_cdp_read_only_isolated_launcher_implementation_preflight(
    vault_root: str | Path,
    gate_approval_id: str,
    *,
    target_url: str | None = None,
    cdp_endpoint: str | None = None,
    runtime: str = "unknown",
    browser_executable_ref: str | None = None,
    profile_parent_ref: str | None = None,
    port_allocation_strategy: str | None = None,
    process_runner_policy: str | None = None,
    cleanup_strategy: str | None = None,
    cdp_client_binding_ref: str | None = None,
    source_command: str | None = None,
) -> dict[str, Any]:
    """Return the no-launch implementation preflight for the future isolated launcher."""
    _validate_gate_approval_id(gate_approval_id)
    launcher_design = build_cdp_read_only_isolated_browser_launcher_design(
        vault_root,
        gate_approval_id,
        target_url=target_url,
        cdp_endpoint=cdp_endpoint,
        runtime=runtime,
        source_command=source_command or "chaseos runtime browser-cdp isolated-launcher-implementation-preflight",
    )
    launcher_design_status = str(launcher_design.get("launcher_design_status") or "unknown")
    approval_status = str(launcher_design.get("approval_status") or "missing")

    executable_supplied = bool(str(browser_executable_ref or "").strip())
    profile_ref_supplied = bool(str(profile_parent_ref or "").strip())
    executable_ref_allowed = executable_supplied and _opaque_launcher_ref_is_allowed(str(browser_executable_ref))
    profile_ref_allowed = profile_ref_supplied and _opaque_launcher_ref_is_allowed(str(profile_parent_ref))
    port_strategy_ok = port_allocation_strategy == "allocate_unused_loopback_port"
    runner_policy_ok = process_runner_policy == "bounded_spawn_no_shell"
    cleanup_strategy_ok = cleanup_strategy == "close_then_delete_throwaway_profile"
    cdp_binding_supplied = bool(str(cdp_client_binding_ref or "").strip())
    cdp_binding_allowed = cdp_binding_supplied and str(cdp_client_binding_ref).startswith("runtime.browser_runtime.")
    live_code_status = _cdp_live_code_status()
    launcher_code_available = bool(live_code_status["launcher_code_available"])
    cdp_client_code_available = bool(live_code_status["cdp_client_code_available"])
    launcher_implementation_status = (
        "implemented_code_path_environment_unverified"
        if launcher_code_available and cdp_client_code_available
        else "not_built"
    )

    component_checks = [
        _precondition(
            "launcher_design_ready",
            passed=launcher_design_status == "ready_for_future_isolated_launcher_but_launcher_not_built",
            status=launcher_design_status,
            reason="implementation preflight requires the launcher design surface to be ready",
        ),
        _precondition(
            "live_launcher_code_present",
            passed=launcher_code_available,
            status="present" if launcher_code_available else "missing",
            reason="runtime.browser_runtime.cdp_live.IsolatedBrowserLauncher must exist before environment smoke",
        ),
        _precondition(
            "live_cdp_client_code_present",
            passed=cdp_client_code_available,
            status="present" if cdp_client_code_available else "missing",
            reason="runtime.browser_runtime.cdp_live.MinimalCDPClient must exist before environment smoke",
        ),
        _precondition(
            "browser_executable_ref_supplied",
            passed=executable_supplied,
            status="supplied" if executable_supplied else "missing",
            reason="future implementation must declare an operator-managed executable reference",
        ),
        _precondition(
            "browser_executable_ref_opaque",
            passed=executable_ref_allowed,
            status="opaque" if executable_ref_allowed else "blocked",
            reason="executable reference must not expose profile, credential, cookie, or history paths",
        ),
        _precondition(
            "profile_parent_ref_supplied",
            passed=profile_ref_supplied,
            status="supplied" if profile_ref_supplied else "missing",
            reason="future implementation must declare an opaque throwaway-profile parent reference",
        ),
        _precondition(
            "profile_parent_ref_opaque",
            passed=profile_ref_allowed,
            status="opaque" if profile_ref_allowed else "blocked",
            reason="profile reference must be opaque and must not be a real browser profile path",
        ),
        _precondition(
            "port_allocation_strategy_loopback_only",
            passed=port_strategy_ok,
            status=port_allocation_strategy or "missing",
            reason="future launcher must allocate an unused loopback-only CDP port",
        ),
        _precondition(
            "process_runner_policy_no_shell",
            passed=runner_policy_ok,
            status=process_runner_policy or "missing",
            reason="future launcher must spawn the browser directly without shell execution",
        ),
        _precondition(
            "cleanup_strategy_throwaway_profile",
            passed=cleanup_strategy_ok,
            status=cleanup_strategy or "missing",
            reason="future launcher must close the process and remove throwaway profile state",
        ),
        _precondition(
            "cdp_client_binding_declared",
            passed=cdp_binding_allowed,
            status="declared" if cdp_binding_allowed else "missing_or_blocked",
            reason="future launcher implementation must name a bounded ChaseOS CDP client binding",
        ),
    ]
    component_ready = all(bool(item.get("passed")) for item in component_checks)

    blocked_reasons = list(dict.fromkeys(launcher_design.get("blocked_reasons") or []))
    if not executable_supplied:
        blocked_reasons.append("browser_cdp_launcher_executable_ref_missing")
    elif not executable_ref_allowed:
        blocked_reasons.append("browser_cdp_launcher_executable_ref_not_opaque")
    if not profile_ref_supplied:
        blocked_reasons.append("browser_cdp_launcher_profile_parent_ref_missing")
    elif not profile_ref_allowed:
        blocked_reasons.append("browser_cdp_launcher_profile_parent_ref_not_opaque")
    if not port_strategy_ok:
        blocked_reasons.append("browser_cdp_loopback_port_allocator_missing")
    if not runner_policy_ok:
        blocked_reasons.append("browser_cdp_no_shell_process_runner_missing")
    if not cleanup_strategy_ok:
        blocked_reasons.append("browser_cdp_throwaway_profile_cleanup_missing")
    if not cdp_binding_allowed:
        blocked_reasons.append("browser_cdp_default_client_binding_missing")
    if not launcher_code_available:
        blocked_reasons.append("browser_cdp_live_launcher_code_missing")
    if not cdp_client_code_available:
        blocked_reasons.append("browser_cdp_live_client_code_missing")

    if launcher_design_status != "ready_for_future_isolated_launcher_but_launcher_not_built":
        preflight_status = launcher_design_status
        next_action = "resolve_launcher_design_blocker_before_implementation"
    elif not component_ready:
        preflight_status = "blocked_launcher_implementation_metadata_incomplete"
        next_action = "supply_opaque_launcher_metadata_before_implementation_patch"
    else:
        preflight_status = "ready_for_launcher_implementation_patch_no_execution"
        next_action = "implement_launcher_with_injected_process_runner_and_keep_default_live_execution_disabled"

    return {
        "ok": True,
        "schema_version": 1,
        "operation": BROWSER_CDP_READ_ONLY_PROOF_OPERATION,
        "approval_schema_id": BROWSER_CDP_READ_ONLY_PROOF_APPROVAL_SCHEMA_ID,
        "gate_approval_id": gate_approval_id,
        "preflight_status": preflight_status,
        "launcher_implementation_status": launcher_implementation_status,
        "implementation_patch_ready": preflight_status == "ready_for_launcher_implementation_patch_no_execution",
        "execution_enabled": False,
        "cdp_read_only_proof_allowed": False,
        "approval_status": approval_status,
        "approval_status_approved": approval_status == "approved",
        "isolated_browser_launcher_design": launcher_design,
        "implementation_contract": {
            "module_boundary": "runtime.browser_runtime.cdp_live",
            "launcher_class": "IsolatedBrowserLauncher",
            "current_launcher_class": "IsolatedBrowserLauncher",
            "current_cdp_client_class": "MinimalCDPClient",
            "process_runner_policy": "bounded_spawn_no_shell",
            "port_allocator_policy": "allocate_unused_loopback_port",
            "profile_policy": "throwaway_only_opaque_ref",
            "default_execution_enabled_after_patch": False,
            "requires_injected_process_runner_for_tests": True,
            "requires_explicit_gate_approval_for_live_use": True,
        },
        "component_checks": component_checks,
        "live_code_status": live_code_status,
        "proposed_launcher_refs": {
            "browser_executable_ref_supplied": executable_supplied,
            "browser_executable_ref_allowed": executable_ref_allowed,
            "profile_parent_ref_supplied": profile_ref_supplied,
            "profile_parent_ref_allowed": profile_ref_allowed,
            "port_allocation_strategy": port_allocation_strategy,
            "process_runner_policy": process_runner_policy,
            "cleanup_strategy": cleanup_strategy,
            "cdp_client_binding_ref_supplied": cdp_binding_supplied,
            "cdp_client_binding_ref_allowed": cdp_binding_allowed,
            "raw_refs_logged": False,
        },
        "acceptance_tests_required": [
            "launcher refuses non-loopback debugging address",
            "launcher refuses existing/real profile references",
            "launcher requires injected process runner in tests",
            "launcher builds command without shell execution",
            "launcher returns only redacted/opaque profile refs",
            "launcher cleanup runs on success and failure",
            "CLI remains disabled for live launch until a separate Gate-approved pass",
        ],
        "forbidden_implementation_fields": [
            "password",
            "api_key",
            "authorization",
            "cookie",
            "session",
            "local_storage",
            "indexed_db",
            "user_data_dir",
            "profile_path",
            "browser_history",
            "extension_state",
            "shell_command",
            "raw_cdp_endpoint_public_host",
        ],
        "blocked_reasons": list(dict.fromkeys(blocked_reasons)),
        "approval_consumed": False,
        "approval_artifact_mutated": False,
        "approval_request_written": False,
        "approval_decision_written": False,
        "idempotency_marker_written": False,
        "marker_directory_created": False,
        "browser_launch_attempted": False,
        "browser_process_spawned": False,
        "throwaway_profile_created": False,
        "cdp_port_opened": False,
        "cdp_connection_attempted": False,
        "screenshot_attempted": False,
        "dom_snapshot_attempted": False,
        "credential_value_read": False,
        "cookie_or_session_read": False,
        "real_profile_used": False,
        "trusted_skill_written": False,
        "canonical_files_mutated": False,
        "agent_bus_task_enqueued": False,
        "provider_call_attempted": False,
        "files_modified": False,
        "next_action": next_action,
        "source_command": source_command,
    }


def format_cdp_decision_preflight(payload: dict[str, Any]) -> str:
    validation = payload.get("approval_validation") if isinstance(payload.get("approval_validation"), dict) else {}
    idempotency = payload.get("idempotency") if isinstance(payload.get("idempotency"), dict) else {}
    lines = [
        "ChaseOS Browser CDP Decision Preflight",
        f"- gate_approval_id: {payload.get('gate_approval_id')}",
        f"- decision_consumption_status: {payload.get('decision_consumption_status')}",
        f"- approval_status: {payload.get('approval_status')}",
        f"- approval_decision_accepted: {payload.get('approval_decision_accepted')}",
        f"- idempotency_marker_exists: {idempotency.get('marker_exists')}",
        f"- executor_status: {payload.get('executor_status')}",
        f"- execution_enabled: {payload.get('execution_enabled')}",
        f"- cdp_read_only_proof_allowed: {payload.get('cdp_read_only_proof_allowed')}",
        f"- approval_consumed: {payload.get('approval_consumed')}",
        f"- browser_launch_attempted: {payload.get('browser_launch_attempted')}",
        f"- cdp_connection_attempted: {payload.get('cdp_connection_attempted')}",
        f"- validation_errors: {validation.get('errors')}",
        f"- next_action: {payload.get('next_action')}",
    ]
    return "\n".join(lines)


def format_cdp_approval_decision_policy(payload: dict[str, Any]) -> str:
    lines = [
        "ChaseOS Browser CDP Approval Decision Policy",
        f"- gate_approval_id: {payload.get('gate_approval_id')}",
        f"- policy_status: {payload.get('policy_status')}",
        f"- approval_status: {payload.get('approval_status')}",
        f"- approval_artifact_structurally_valid: {payload.get('approval_artifact_structurally_valid')}",
        f"- approval_decision_metadata_present: {payload.get('approval_decision_metadata_present')}",
        f"- approval_decision_accepted: {payload.get('approval_decision_accepted')}",
        f"- approval_consumed: {payload.get('approval_consumed')}",
        f"- idempotency_marker_written: {payload.get('idempotency_marker_written')}",
        f"- browser_launch_attempted: {payload.get('browser_launch_attempted')}",
        f"- cdp_connection_attempted: {payload.get('cdp_connection_attempted')}",
        f"- files_modified: {payload.get('files_modified')}",
        f"- next_action: {payload.get('next_action')}",
    ]
    return "\n".join(lines)


def format_cdp_approval_decision_consumer_design(payload: dict[str, Any]) -> str:
    idempotency = payload.get("idempotency") if isinstance(payload.get("idempotency"), dict) else {}
    lines = [
        "ChaseOS Browser CDP Approval Decision Consumer Design",
        f"- gate_approval_id: {payload.get('gate_approval_id')}",
        f"- consumer_design_status: {payload.get('consumer_design_status')}",
        f"- consumer_status: {payload.get('consumer_status')}",
        f"- approval_status: {payload.get('approval_status')}",
        f"- approval_decision_accepted: {payload.get('approval_decision_accepted')}",
        f"- approval_consumed: {payload.get('approval_consumed')}",
        f"- approval_decision_written: {payload.get('approval_decision_written')}",
        f"- idempotency_marker_exists: {idempotency.get('marker_exists')}",
        f"- idempotency_marker_written: {payload.get('idempotency_marker_written')}",
        f"- browser_launch_attempted: {payload.get('browser_launch_attempted')}",
        f"- cdp_connection_attempted: {payload.get('cdp_connection_attempted')}",
        f"- files_modified: {payload.get('files_modified')}",
        f"- next_action: {payload.get('next_action')}",
    ]
    return "\n".join(lines)


def format_cdp_isolated_browser_launcher_design(payload: dict[str, Any]) -> str:
    contract = payload.get("launcher_contract") if isinstance(payload.get("launcher_contract"), dict) else {}
    lines = [
        "ChaseOS Browser CDP Isolated Browser Launcher Design",
        f"- gate_approval_id: {payload.get('gate_approval_id')}",
        f"- launcher_design_status: {payload.get('launcher_design_status')}",
        f"- launcher_status: {payload.get('launcher_status')}",
        f"- launch_strategy: {payload.get('launch_strategy')}",
        f"- browser_profile_policy: {payload.get('browser_profile_policy')}",
        f"- debugging_address: {contract.get('debugging_address')}",
        f"- profile_strategy: {contract.get('profile_strategy')}",
        f"- browser_launch_attempted: {payload.get('browser_launch_attempted')}",
        f"- browser_process_spawned: {payload.get('browser_process_spawned')}",
        f"- throwaway_profile_created: {payload.get('throwaway_profile_created')}",
        f"- cdp_port_opened: {payload.get('cdp_port_opened')}",
        f"- cdp_connection_attempted: {payload.get('cdp_connection_attempted')}",
        f"- files_modified: {payload.get('files_modified')}",
        f"- next_action: {payload.get('next_action')}",
    ]
    return "\n".join(lines)


def format_cdp_isolated_launcher_implementation_preflight(payload: dict[str, Any]) -> str:
    refs = payload.get("proposed_launcher_refs") if isinstance(payload.get("proposed_launcher_refs"), dict) else {}
    lines = [
        "ChaseOS Browser CDP Isolated Launcher Implementation Preflight",
        f"- gate_approval_id: {payload.get('gate_approval_id')}",
        f"- preflight_status: {payload.get('preflight_status')}",
        f"- launcher_implementation_status: {payload.get('launcher_implementation_status')}",
        f"- implementation_patch_ready: {payload.get('implementation_patch_ready')}",
        f"- approval_status: {payload.get('approval_status')}",
        f"- browser_executable_ref_supplied: {refs.get('browser_executable_ref_supplied')}",
        f"- profile_parent_ref_supplied: {refs.get('profile_parent_ref_supplied')}",
        f"- cdp_client_binding_ref_supplied: {refs.get('cdp_client_binding_ref_supplied')}",
        f"- execution_enabled: {payload.get('execution_enabled')}",
        f"- browser_launch_attempted: {payload.get('browser_launch_attempted')}",
        f"- browser_process_spawned: {payload.get('browser_process_spawned')}",
        f"- throwaway_profile_created: {payload.get('throwaway_profile_created')}",
        f"- cdp_port_opened: {payload.get('cdp_port_opened')}",
        f"- cdp_connection_attempted: {payload.get('cdp_connection_attempted')}",
        f"- files_modified: {payload.get('files_modified')}",
        f"- next_action: {payload.get('next_action')}",
    ]
    return "\n".join(lines)


def format_cdp_atomic_marker_writer_design(payload: dict[str, Any]) -> str:
    idempotency = payload.get("idempotency") if isinstance(payload.get("idempotency"), dict) else {}
    lines = [
        "ChaseOS Browser CDP Atomic Marker Writer Design",
        f"- gate_approval_id: {payload.get('gate_approval_id')}",
        f"- writer_design_status: {payload.get('writer_design_status')}",
        f"- writer_status: {payload.get('writer_status')}",
        f"- approval_status: {payload.get('approval_status')}",
        f"- approval_decision_accepted: {payload.get('approval_decision_accepted')}",
        f"- approval_consumed: {payload.get('approval_consumed')}",
        f"- idempotency_marker_exists: {idempotency.get('marker_exists')}",
        f"- idempotency_marker_written: {payload.get('idempotency_marker_written')}",
        f"- marker_directory_created: {payload.get('marker_directory_created')}",
        f"- browser_launch_attempted: {payload.get('browser_launch_attempted')}",
        f"- cdp_connection_attempted: {payload.get('cdp_connection_attempted')}",
        f"- files_modified: {payload.get('files_modified')}",
        f"- next_action: {payload.get('next_action')}",
    ]
    return "\n".join(lines)


def format_cdp_executor_dry_run_plan(payload: dict[str, Any]) -> str:
    idempotency = payload.get("idempotency") if isinstance(payload.get("idempotency"), dict) else {}
    tracker = (
        payload.get("feature_completion_tracker")
        if isinstance(payload.get("feature_completion_tracker"), dict)
        else {}
    )
    lines = [
        "ChaseOS Browser CDP Executor Dry-Run Plan",
        f"- gate_approval_id: {payload.get('gate_approval_id')}",
        f"- dry_run_status: {payload.get('dry_run_status')}",
        f"- dry_run_only: {payload.get('dry_run_only')}",
        f"- approval_status: {payload.get('approval_status')}",
        f"- idempotency_marker_exists: {idempotency.get('marker_exists')}",
        f"- idempotency_marker_written: {payload.get('idempotency_marker_written')}",
        f"- executor_status: {payload.get('executor_status')}",
        f"- execution_enabled: {payload.get('execution_enabled')}",
        f"- browser_launch_attempted: {payload.get('browser_launch_attempted')}",
        f"- cdp_connection_attempted: {payload.get('cdp_connection_attempted')}",
        f"- pre_execution_governance_status: {tracker.get('pre_execution_governance_status')}",
        f"- live_cdp_execution_status: {tracker.get('live_cdp_execution_status')}",
        f"- next_action: {payload.get('next_action')}",
    ]
    return "\n".join(lines)


def format_cdp_idempotency_reservation_spec(payload: dict[str, Any]) -> str:
    idempotency = payload.get("idempotency") if isinstance(payload.get("idempotency"), dict) else {}
    lines = [
        "ChaseOS Browser CDP Idempotency Reservation Spec",
        f"- gate_approval_id: {payload.get('gate_approval_id')}",
        f"- reservation_status: {payload.get('reservation_status')}",
        f"- approval_status: {payload.get('approval_status')}",
        f"- idempotency_marker_exists: {idempotency.get('marker_exists')}",
        f"- idempotency_marker_written: {payload.get('idempotency_marker_written')}",
        f"- executor_status: {payload.get('executor_status')}",
        f"- execution_enabled: {payload.get('execution_enabled')}",
        f"- approval_consumed: {payload.get('approval_consumed')}",
        f"- browser_launch_attempted: {payload.get('browser_launch_attempted')}",
        f"- cdp_connection_attempted: {payload.get('cdp_connection_attempted')}",
        f"- files_modified: {payload.get('files_modified')}",
        f"- next_action: {payload.get('next_action')}",
    ]
    return "\n".join(lines)


def approval_artifacts_dir(vault_root: str | Path) -> Path:
    return Path(vault_root) / APPROVAL_RELATIVE_DIR


def cdp_read_only_idempotency_marker_path(vault_root: str | Path, gate_approval_id: str) -> Path:
    _validate_gate_approval_id(gate_approval_id)
    base = (Path(vault_root) / IDEMPOTENCY_MARKER_RELATIVE_DIR).resolve()
    path = (Path(vault_root) / IDEMPOTENCY_MARKER_RELATIVE_DIR / f"{gate_approval_id}.json").resolve()
    try:
        path.relative_to(base)
    except ValueError as exc:
        raise BrowserCDPExecutorSpecError(f"CDP idempotency marker path escapes marker directory: {path}") from exc
    return path


def build_cdp_read_only_approval_request_record(
    spec: dict[str, Any],
    *,
    requested_by: str,
    operator_request_id: str | None = None,
    gate_approval_id: str | None = None,
    source_command: str | None = None,
) -> dict[str, Any]:
    """Build a pending CDP read-only proof approval request record."""
    gate_approval_id = gate_approval_id or _new_gate_approval_id()
    _validate_gate_approval_id(gate_approval_id)
    operator_request_id = operator_request_id or _new_operator_request_id()
    schema = spec.get("approval_schema") or {}
    template = schema.get("approval_request_template") or {}
    record = {
        "record_type": "browser_cdp_read_only_proof_approval_request",
        "schema_version": 1,
        "approval_schema_id": BROWSER_CDP_READ_ONLY_PROOF_APPROVAL_SCHEMA_ID,
        "operation": BROWSER_CDP_READ_ONLY_PROOF_OPERATION,
        "operator_request_id": str(operator_request_id),
        "gate_approval_id": gate_approval_id,
        "runtime": str(spec.get("runtime") or template.get("runtime") or "unknown"),
        "target_url": str(spec.get("target_url") or template.get("target_url") or ""),
        "allowed_domains": list(spec.get("allowed_domains") or template.get("allowed_domains") or []),
        "cdp_endpoint": str(spec.get("cdp_endpoint") or template.get("cdp_endpoint") or ""),
        "launch_strategy": str(template.get("launch_strategy") or "chaseos_launch_isolated"),
        "browser_profile_policy": str(template.get("browser_profile_policy") or "throwaway_only"),
        "allowed_actions": list(template.get("allowed_actions") or []),
        "artifact_targets": list(template.get("artifact_targets") or []),
        "screenshot_retention": str(template.get("screenshot_retention") or "log_artifact_only_redacted_if_needed"),
        "secret_policy": dict(template.get("secret_policy") or {}),
        "status": "pending",
        "requested_by": str(requested_by or "operator"),
        "requested_at": _utc_now(),
        "approved_by": None,
        "approved_at": None,
        "approval_effect": (
            "Records operator intent to review one future local read-only CDP proof. "
            "This artifact does not launch a browser, connect to CDP, or authorize execution."
        ),
        "browser_launch_attempted": False,
        "cdp_connection_attempted": False,
        "screenshot_attempted": False,
        "dom_snapshot_attempted": False,
        "credential_value_read": False,
        "cookie_or_session_read": False,
        "real_profile_used": False,
        "trusted_skill_written": False,
        "canonical_files_mutated": False,
        "source_command": source_command,
    }
    record["request_digest_sha256"] = _approval_digest(record)
    return record


def write_cdp_read_only_approval_request(
    vault_root: str | Path,
    *,
    target_url: str | None = None,
    runtime: str = "unknown",
    requested_by: str = "operator",
    source_command: str | None = None,
) -> dict[str, Any]:
    """Persist a pending CDP read-only proof approval request without execution."""
    spec = build_cdp_read_only_executor_spec(
        vault_root=vault_root,
        target_url=target_url,
        runtime=runtime,
        source_command=source_command or "chaseos runtime browser-cdp approval-request",
    )
    if not (spec.get("cdp_design_preflight") or {}).get("ok"):
        raise BrowserCDPExecutorSpecError("CDP approval request requires a local, design-preflight-ready target")
    record = build_cdp_read_only_approval_request_record(
        spec,
        requested_by=requested_by,
        source_command=source_command,
    )
    path = _approval_artifact_path(vault_root, str(record["gate_approval_id"]))
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise BrowserCDPExecutorSpecError(f"CDP approval request already exists: {record['gate_approval_id']}")
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    validation = validate_cdp_read_only_approval_artifact(
        vault_root,
        str(record["gate_approval_id"]),
        expected_target_url=record["target_url"],
        expected_runtime=record["runtime"],
    )
    return {
        "ok": True,
        "record_type": "browser_cdp_read_only_proof_approval_request_result",
        "approval_request_written": True,
        "approval_ref": str(path),
        "gate_approval_id": record["gate_approval_id"],
        "operator_request_id": record["operator_request_id"],
        "approval_status": record["status"],
        "request_digest_sha256": record["request_digest_sha256"],
        "browser_launch_attempted": False,
        "cdp_connection_attempted": False,
        "credential_value_read": False,
        "cookie_or_session_read": False,
        "trusted_skill_written": False,
        "canonical_files_mutated": False,
        "approval_validation": validation,
        "executor_spec": spec,
        "record": record,
    }


def validate_cdp_read_only_approval_artifact(
    vault_root: str | Path | None,
    gate_approval_id: str | None,
    *,
    expected_target_url: str | None = None,
    expected_runtime: str | None = None,
) -> dict[str, Any]:
    """Validate a pending CDP approval request artifact without consuming it."""
    if not gate_approval_id:
        return _approval_validation(None, artifact_store_implemented=True)
    _validate_gate_approval_id(gate_approval_id)
    if vault_root is None:
        return _approval_validation(
            gate_approval_id,
            artifact_store_implemented=True,
            artifact_lookup_attempted=False,
            reason="vault_root not supplied; approval artifact lookup skipped",
        )

    path = _approval_artifact_path(vault_root, gate_approval_id)
    if not path.exists():
        return _approval_validation(
            gate_approval_id,
            artifact_store_implemented=True,
            artifact_lookup_attempted=True,
            reason=f"approval artifact not found: {gate_approval_id}",
        )
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return _approval_validation(
            gate_approval_id,
            artifact_store_implemented=True,
            artifact_lookup_attempted=True,
            reason=f"invalid approval artifact JSON: {exc}",
        )
    if not isinstance(record, dict):
        return _approval_validation(
            gate_approval_id,
            artifact_store_implemented=True,
            artifact_lookup_attempted=True,
            reason="approval artifact must be a JSON object",
        )

    errors: list[str] = []
    if record.get("record_type") != "browser_cdp_read_only_proof_approval_request":
        errors.append("record_type mismatch")
    if record.get("approval_schema_id") != BROWSER_CDP_READ_ONLY_PROOF_APPROVAL_SCHEMA_ID:
        errors.append("approval_schema_id mismatch")
    if record.get("operation") != BROWSER_CDP_READ_ONLY_PROOF_OPERATION:
        errors.append("operation mismatch")
    if record.get("gate_approval_id") != gate_approval_id:
        errors.append("gate_approval_id mismatch")
    status = str(record.get("status") or "")
    if status not in APPROVAL_STATUSES:
        errors.append("invalid status")
    for field_name in BROWSER_CDP_READ_ONLY_PROOF_APPROVAL_REQUIRED_FIELDS:
        if field_name not in record:
            errors.append(f"missing required field: {field_name}")
    expected_digest = record.get("request_digest_sha256")
    if not expected_digest or expected_digest != _approval_digest(record):
        errors.append("request digest mismatch")
    if expected_target_url and record.get("target_url") != expected_target_url:
        errors.append("target_url mismatch")
    if expected_runtime and record.get("runtime") != expected_runtime:
        errors.append("runtime mismatch")

    structurally_valid = not errors
    return {
        "gate_approval_id": gate_approval_id,
        "artifact_supplied": True,
        "artifact_store_implemented": True,
        "artifact_lookup_attempted": True,
        "artifact_ref": str(path),
        "structurally_valid": structurally_valid,
        "matches_preflight": structurally_valid,
        "approval_status": status or "unknown",
        "approved_by": record.get("approved_by"),
        "approved_at": record.get("approved_at"),
        "approval_decision_accepted": False,
        "cdp_read_only_proof_allowed": False,
        "errors": errors,
        "request_digest_sha256": record.get("request_digest_sha256"),
        "reason": "approval artifact is structurally valid" if structurally_valid else "; ".join(errors),
        "browser_launch_attempted": False,
        "cdp_connection_attempted": False,
        "credential_value_read": False,
        "cookie_or_session_read": False,
        "trusted_skill_written": False,
        "canonical_files_mutated": False,
    }


def _allowed_domains_for_target(target_url: str) -> list[str]:
    if "localhost" in target_url:
        return ["localhost"]
    if "::1" in target_url:
        return ["::1"]
    return ["127.0.0.1"]


def _approval_validation(
    gate_approval_id: str | None,
    *,
    artifact_store_implemented: bool,
    artifact_lookup_attempted: bool = False,
    reason: str | None = None,
) -> dict[str, Any]:
    return {
        "gate_approval_id": gate_approval_id,
        "artifact_supplied": bool(gate_approval_id),
        "artifact_store_implemented": artifact_store_implemented,
        "artifact_lookup_attempted": artifact_lookup_attempted,
        "structurally_valid": False,
        "approval_status": "not_checked",
        "approval_decision_accepted": False,
        "cdp_read_only_proof_allowed": False,
        "reason": reason or "approval artifact not supplied",
    }


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _validate_gate_approval_id(gate_approval_id: str) -> None:
    if not _SAFE_GATE_APPROVAL_ID.match(str(gate_approval_id or "")):
        raise BrowserCDPExecutorSpecError(f"unsafe gate_approval_id: {gate_approval_id!r}")


def _approval_artifact_path(vault_root: str | Path, gate_approval_id: str) -> Path:
    _validate_gate_approval_id(gate_approval_id)
    base = approval_artifacts_dir(vault_root).resolve()
    path = (approval_artifacts_dir(vault_root) / f"{gate_approval_id}.json").resolve()
    try:
        path.relative_to(base)
    except ValueError as exc:
        raise BrowserCDPExecutorSpecError(f"CDP approval artifact path escapes approval directory: {path}") from exc
    return path


def _future_cdp_write_plan(spec: dict[str, Any], gate_approval_id: str) -> dict[str, Any]:
    target = str(spec.get("target_url") or DEFAULT_LOCAL_TARGET_URL)
    domain_slug = _domain_slug(_allowed_domains_for_target(target)[0])
    safe_id = gate_approval_id.replace(".", "-")
    targets = [
        {
            "target_id": "browser_run_log",
            "path": f"07_LOGS/Browser-Runs/cdp-read-only-proof-{safe_id}.json",
            "write_enabled_after_approval": True,
            "content_policy": "redacted_run_evidence_no_credentials_no_cookies_no_session_tokens",
        },
        {
            "target_id": "agent_activity_log",
            "path": f"07_LOGS/Agent-Activity/cdp-read-only-proof-{safe_id}.md",
            "write_enabled_after_approval": True,
            "content_policy": "operator_visible_activity_summary_no_private_profile_state",
        },
        {
            "target_id": "screenshot_artifact",
            "path": f"07_LOGS/Operator-Screenshots/cdp-read-only-proof-{safe_id}.png",
            "write_enabled_after_approval": True,
            "content_policy": "local_public_or_non_sensitive_page_only_redact_or_discard_if_needed",
        },
        {
            "target_id": "untrusted_skill_candidate",
            "path": f"03_INPUTS/Browser-Skill-Candidates/{domain_slug}/cdp-read-only-proof-{safe_id}.md",
            "write_enabled_after_approval": True,
            "content_policy": "tier4_untrusted_candidate_data_not_executable",
        },
    ]
    return {
        "write_plan_status": "planned_no_write",
        "writes_attempted": False,
        "target_url": target,
        "targets": targets,
        "denied_targets": [
            "runtime/browser_skills/skills/",
            "06_AGENTS/Browser-Skills/",
            "00_HOME/",
            "01_PROJECTS/",
            "02_KNOWLEDGE/",
            "runtime/policy/",
        ],
        "forbidden_payload_fields": [
            "password",
            "api_key",
            "authorization",
            "cookie",
            "session",
            "local_storage",
            "indexed_db",
            "user_data_dir",
            "profile_path",
            "browser_history",
        ],
    }


def _future_write_plan_is_limited(write_plan: dict[str, Any]) -> bool:
    allowed_prefixes = (
        "07_LOGS/Browser-Runs/",
        "07_LOGS/Agent-Activity/",
        "07_LOGS/Operator-Screenshots/",
        "03_INPUTS/Browser-Skill-Candidates/",
    )
    targets = write_plan.get("targets") if isinstance(write_plan, dict) else []
    if not isinstance(targets, list) or not targets:
        return False
    return all(str(item.get("path") or "").startswith(allowed_prefixes) for item in targets if isinstance(item, dict))


def _opaque_launcher_ref_is_allowed(value: str) -> bool:
    lowered = str(value or "").strip().lower()
    if not lowered:
        return False
    if not (
        lowered.startswith("chaseos-managed://")
        or lowered.startswith("chaseos-temp://")
        or lowered.startswith("runtime.browser_runtime.")
    ):
        return False
    forbidden_fragments = (
        "password",
        "credential",
        "cookie",
        "session",
        "history",
        "local storage",
        "local_storage",
        "indexeddb",
        "indexed_db",
        "user data",
        "user_data",
        "profile/default",
        "profile\\default",
        "appdata",
        "chrome/default",
        "chrome\\default",
    )
    return not any(fragment in lowered for fragment in forbidden_fragments)


def _cdp_live_code_status() -> dict[str, Any]:
    try:
        from runtime.browser_runtime.cdp_live import IsolatedBrowserLauncher, MinimalCDPClient

        return {
            "launcher_code_available": callable(IsolatedBrowserLauncher),
            "cdp_client_code_available": callable(MinimalCDPClient),
            "module": "runtime.browser_runtime.cdp_live",
            "environment_checked": False,
            "browser_executable_checked": False,
            "browser_launch_attempted": False,
            "cdp_connection_attempted": False,
        }
    except Exception as exc:
        return {
            "launcher_code_available": False,
            "cdp_client_code_available": False,
            "module": "runtime.browser_runtime.cdp_live",
            "environment_checked": False,
            "browser_executable_checked": False,
            "browser_launch_attempted": False,
            "cdp_connection_attempted": False,
            "error": str(exc),
        }


def _browser_cdp_operational_activation_evidence(vault_root: str | Path) -> dict[str, Any]:
    root = Path(vault_root)
    evidence_path = root / OPERATIONAL_ACTIVATION_BUILD_LOG_RELATIVE_PATH
    exists = evidence_path.is_file()
    content = evidence_path.read_text(encoding="utf-8") if exists else ""
    required_markers = [
        "implemented_cdp_read_only_proof_complete",
        "approval_consumed: True",
        "idempotency_marker_written: True",
        "browser_launch_attempted: True",
        "cdp_connection_attempted: True",
        "screenshot_attempted: True",
        "dom_snapshot_attempted: True",
    ]
    markers_present = {marker: marker in content for marker in required_markers}
    operationally_activated = bool(exists and all(markers_present.values()))
    return {
        "evidence_type": "build_log",
        "evidence_path": OPERATIONAL_ACTIVATION_BUILD_LOG_RELATIVE_PATH.as_posix(),
        "evidence_exists": exists,
        "markers_present": markers_present,
        "operationally_activated": operationally_activated,
        "raw_evidence_copied": False,
        "browser_launch_attempted_by_check": False,
        "cdp_connection_attempted_by_check": False,
        "files_modified": False,
    }


def _domain_slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", str(value).strip().lower()).strip("-")
    return slug or "local"


def _approval_digest(record: dict[str, Any]) -> str:
    material = {
        key: value
        for key, value in record.items()
        if key not in {"request_digest_sha256", "approval_ref", "audit_id"}
    }
    canonical = json.dumps(material, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _new_gate_approval_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"bosl-cdp-appr-{stamp}-{uuid.uuid4().hex[:8]}"


def _new_operator_request_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"bosl-cdp-req-{stamp}-{uuid.uuid4().hex[:8]}"


def _precondition(
    precondition_id: str,
    *,
    passed: bool,
    status: str,
    reason: str,
    evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "precondition_id": precondition_id,
        "passed": passed,
        "status": status,
        "reason": reason,
        "evidence": evidence or {},
    }
