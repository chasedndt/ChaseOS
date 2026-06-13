"""Read-only Pass 10B expansion-pack completion audit.

This audit answers whether the current Pass 10B expansion-pack lane is truly
closed by composing existing evidence surfaces. It does not consume approvals,
reserve exact-once markers, build installer output, launch apps, call providers,
write Agent Bus tasks, mutate host/release state, or write canonical state.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from runtime.studio.full_desktop_card_ui_inventory_proof import (
    build_full_desktop_card_ui_inventory_proof,
)
from runtime.studio.installer_build_approval_consumption_dry_run import (
    build_studio_installer_build_approval_consumption_dry_run,
)
from runtime.studio.installer_build_approval_review import (
    build_studio_installer_build_approval_review,
)
from runtime.studio.installer_build_approved_execution_proof import (
    build_studio_installer_build_approved_execution_proof,
)
from runtime.studio.installer_plan import build_studio_installer_plan


MODEL_VERSION = "studio.pass10b_expansion_pack_completion_audit.v1"
SURFACE_ID = "studio_pass10b_expansion_pack_completion_audit"
DEFAULT_REPORT_ROOT = Path("07_LOGS") / "Studio-Graph-Views" / "pass10b-expansion-pack-completion-audits"
DEFAULT_HANDOFF_ROOT = DEFAULT_REPORT_ROOT
DEFAULT_APPROVAL_PACKET_ID = "studio-installer-build-appr-ac14811da651baec"
COMPLETE_STATUS = "COMPLETE / VERIFIED"
PARTIAL_STATUS = "PARTIAL / READY_FOR_EXPLICIT_INSTALLER_EXECUTION / NOT COMPLETE"
BLOCKED_STATUS = "BLOCKED / EVIDENCE INCOMPLETE"
HANDOFF_INTEGRITY_STATUS = "VERIFIED / HANDOFF INTEGRITY MATCH / NO EXECUTION"
HANDOFF_INTEGRITY_BLOCKED_STATUS = "BLOCKED / HANDOFF INTEGRITY MISMATCH"
NEXT_EXECUTION_PASS = "studio-installer-build-approved-execution-proof --execute"
NEXT_SIGNING_APPROVAL_PASS = "studio-signing-approval-preview"
EXECUTION_COMMAND_TEMPLATE = (
    "python -m runtime.cli.main studio installer-build-approved-execution-proof "
    "--approval-packet-id {approval_packet_id} --execute --write-evidence --json"
)
POST_EXECUTION_AUDIT_COMMAND_TEMPLATE = (
    "python -m runtime.cli.main studio pass10b-expansion-pack-completion-audit "
    "--approval-packet-id {approval_packet_id} --write-report "
    "--report-slug 2026-05-12-pass10b-expansion-pack-post-execution-audit --json"
)

FORBIDDEN_AUTHORITY_KEYS = (
    "signs_artifacts",
    "reads_signing_certificate",
    "writes_host_startup",
    "registers_autostart",
    "writes_registry",
    "writes_start_menu",
    "writes_desktop_shortcut",
    "promotes_release",
    "writes_release_status",
    "launches_pywebview",
    "starts_servers",
    "launches_executable",
    "browser_use_cli_live_run",
    "excalidraw_live_proof",
    "mutates_gate",
    "executes_workflows",
    "provider_calls_allowed",
    "connector_calls_allowed",
    "writes_agent_bus_tasks",
    "canonical_mutation_allowed",
)


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _relative_to_vault(vault: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(vault.resolve()).as_posix()
    except ValueError:
        return str(path)


def _resolve_vault_relative(vault: Path, path_value: str | Path) -> Path:
    path = Path(path_value)
    resolved = path.resolve() if path.is_absolute() else (vault / path).resolve()
    try:
        resolved.relative_to(vault.resolve())
    except ValueError as exc:
        raise ValueError(f"Pass 10B expansion-pack audit path escapes vault: {path_value}") from exc
    return resolved


def _path_record(vault: Path, path_value: str | Path | None) -> dict[str, Any]:
    if not path_value:
        return {"path": None, "exists": False, "is_file": False, "size_bytes": 0}
    try:
        path = _resolve_vault_relative(vault, path_value)
    except ValueError:
        return {"path": str(path_value), "exists": False, "is_file": False, "size_bytes": 0, "inside_vault": False}
    return {
        "path": _relative_to_vault(vault, path),
        "exists": path.exists(),
        "is_file": path.is_file(),
        "size_bytes": path.stat().st_size if path.is_file() else 0,
        "inside_vault": True,
    }


def _item(
    item_id: str,
    requirement: str,
    *,
    ok: bool,
    status: str,
    evidence: dict[str, Any],
    blocker: str | None = None,
) -> dict[str, Any]:
    row = {
        "id": item_id,
        "requirement": requirement,
        "ok": bool(ok),
        "status": status,
        "evidence": evidence,
    }
    if blocker:
        row["blocker"] = blocker
    return row


def _installer_pass10b_evidence(installer_plan: dict[str, Any]) -> dict[str, Any]:
    return ((installer_plan.get("evidence") or {}).get("pass10b_completion_audit") or {})


def _forbidden_authority_clear(*reports: dict[str, Any]) -> bool:
    for report in reports:
        authority = report.get("authority") or {}
        for key in FORBIDDEN_AUTHORITY_KEYS:
            if authority.get(key) is True:
                return False
    return True


def _execution_performed(execution_proof: dict[str, Any]) -> bool:
    summary = execution_proof.get("summary") or {}
    return bool(summary.get("execution_performed") or summary.get("already_executed"))


def _execution_outputs_present(execution_proof: dict[str, Any]) -> bool:
    paths = execution_proof.get("paths") or {}
    required = ("exact_once_marker", "portable_zip", "build_manifest", "execution_evidence")
    return all(bool((paths.get(key) or {}).get("exists")) for key in required)


def _operator_execution_handoff(
    *,
    approval_packet_id: str,
    ready_for_execution: bool,
    approved_execution_performed: bool,
    execution_paths: dict[str, Any],
) -> dict[str, Any]:
    status = (
        "EXECUTION_COMPLETE"
        if approved_execution_performed
        else "READY_FOR_OPERATOR_APPROVAL"
        if ready_for_execution
        else "NOT_READY"
    )
    return {
        "status": status,
        "requires_explicit_operator_approval": not approved_execution_performed,
        "approval_statement": (
            "Explicitly approve running the Studio installer-build approved execution proof for "
            f"`{approval_packet_id}` with `--execute`."
        ),
        "execution_command": EXECUTION_COMMAND_TEMPLATE.format(approval_packet_id=approval_packet_id),
        "post_execution_audit_command": POST_EXECUTION_AUDIT_COMMAND_TEMPLATE.format(approval_packet_id=approval_packet_id),
        "expected_writes_if_approved": {
            "exact_once_marker": execution_paths.get("exact_once_marker"),
            "output_root": execution_paths.get("output_root"),
            "portable_zip": execution_paths.get("portable_zip"),
            "build_manifest": execution_paths.get("build_manifest"),
            "pre_output_audit": execution_paths.get("pre_output_audit"),
            "post_output_audit": execution_paths.get("post_output_audit"),
            "dry_run_evidence": execution_paths.get("dry_run_evidence"),
            "execution_evidence": execution_paths.get("execution_evidence"),
        },
        "forbidden_even_if_approved": [
            "signing artifacts",
            "reading signing certificates",
            "startup/autostart mutation",
            "registry writes",
            "Start Menu or desktop shortcut writes",
            "release promotion",
            "host policy mutation",
            "provider or connector calls",
            "Agent Bus task writes",
            "Gate/Git/workflow mutation",
            "canonical ChaseOS mutation",
        ],
        "duplicate_policy": "future execution must block before installer output if the exact-once marker already exists",
    }


def build_pass10b_expansion_pack_completion_audit(
    vault_root: str | Path,
    *,
    approval_packet_id: str | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Build the read-only completion audit from current repo evidence."""

    vault = _vault_path(vault_root)
    timestamp = generated_at or _now_utc()
    packet_id = approval_packet_id or DEFAULT_APPROVAL_PACKET_ID

    installer_plan = build_studio_installer_plan(vault)
    approval_review = build_studio_installer_build_approval_review(
        vault,
        approval_packet_id=packet_id,
        decision="approve",
        write_approval=False,
        generated_at=timestamp,
    )
    consumption_dry_run = build_studio_installer_build_approval_consumption_dry_run(
        vault,
        approval_packet_id=packet_id,
        generated_at=timestamp,
    )
    execution_proof = build_studio_installer_build_approved_execution_proof(
        vault,
        approval_packet_id=packet_id,
        execute=False,
        generated_at=timestamp,
    )
    card_inventory = build_full_desktop_card_ui_inventory_proof(vault, generated_at=timestamp)

    pass10b_evidence = _installer_pass10b_evidence(installer_plan)
    review_summary = approval_review.get("summary") or {}
    dry_summary = consumption_dry_run.get("summary") or {}
    execution_summary = execution_proof.get("summary") or {}
    card_summary = card_inventory.get("summary") or {}
    card_claim = card_inventory.get("claim_decision") or {}
    card_sources = card_inventory.get("source_references") or {}
    execution_paths = execution_proof.get("paths") or {}

    marker_record = execution_paths.get("exact_once_marker") or {}
    output_root_record = execution_paths.get("output_root") or {}
    portable_zip_record = execution_paths.get("portable_zip") or {}
    manifest_record = execution_paths.get("build_manifest") or {}
    execution_evidence_record = execution_paths.get("execution_evidence") or {}

    visual_green = bool(
        installer_plan.get("ok")
        and pass10b_evidence.get("exists") is True
        and pass10b_evidence.get("ok") is True
        and pass10b_evidence.get("native_packaged_visual_qa_complete") is True
        and pass10b_evidence.get("packaged_visual_qa_saved_report_valid") is True
    )
    approval_ready = bool(
        approval_review.get("ok")
        and review_summary.get("approval_artifact_written") is True
        and review_summary.get("future_single_build_approved") is True
        and (
            review_summary.get("approval_decision_consumed") is False
            or review_summary.get("approved_execution_proof_complete") is True
        )
    )
    dry_run_ready = bool(
        consumption_dry_run.get("ok")
        and dry_summary.get("approval_digest_matches") is True
        and dry_summary.get("marker_reservation_proof_passed") is True
        and dry_summary.get("duplicate_consumption_blocked") is True
        and (
            dry_summary.get("approval_consumed") is False
            or dry_summary.get("approved_execution_proof_complete") is True
        )
    )
    readiness_ready = bool(
        execution_proof.get("ok")
        and (
            (
                execution_summary.get("execution_requested") is False
                and execution_summary.get("execution_performed") is False
                and execution_summary.get("approval_consumed") is False
                and execution_summary.get("future_output_paths_clear") is True
            )
            or (
                execution_summary.get("already_executed") is True
                and execution_summary.get("approval_consumed") is True
                and execution_summary.get("duplicate_execution_blocked") is True
            )
        )
    )
    approved_execution_performed = _execution_performed(execution_proof)
    installer_outputs_present = _execution_outputs_present(execution_proof)
    card_inventory_current = bool(
        card_inventory.get("ok")
        and (card_summary.get("pass10b_current_green") is True or card_summary.get("pass10b_current_ok") is True)
        and card_summary.get("live_registry_mounted_panel_count", 0) > 0
    )
    webview2_historical = bool(
        (
            (card_inventory.get("evidence") or {}).get("latest_webview2_operator_remediation_packet")
            or card_sources.get("latest_webview2_operator_remediation_packet")
            or {}
        ).get("exists")
    )
    forbidden_authority_clear = _forbidden_authority_clear(
        approval_review,
        consumption_dry_run,
        execution_proof,
        card_inventory,
    )
    approved_execution_state_valid = bool(
        approved_execution_performed
        and installer_outputs_present
        and execution_summary.get("approval_consumed") is True
        and execution_summary.get("duplicate_execution_blocked") is True
    )
    execution_absent = not approved_execution_performed and not installer_outputs_present
    execution_mutation_authorized = execution_absent or approved_execution_state_valid
    no_forbidden_mutation = bool(forbidden_authority_clear and execution_mutation_authorized)

    checklist = [
        _item(
            "pass10b_visual_proof_current",
            "Current installer lane selects a verified complete Pass 10B visual audit.",
            ok=visual_green,
            status="VERIFIED" if visual_green else "BLOCKED",
            evidence={
                "installer_plan_status": installer_plan.get("status"),
                "pass10b_audit_path": pass10b_evidence.get("path"),
                "pass10b_status": pass10b_evidence.get("status"),
            },
        ),
        _item(
            "installer_build_approval_artifact_written",
            "Scoped installer-build approval artifact exists and matches the current packet.",
            ok=approval_ready,
            status="VERIFIED" if approval_ready else "BLOCKED",
            evidence={
                "approval_packet_id": review_summary.get("approval_packet_id"),
                "approval_artifact_written": review_summary.get("approval_artifact_written"),
                "request_digest_sha256": review_summary.get("request_digest_sha256"),
            },
        ),
        _item(
            "installer_build_consumption_dry_run_verified",
            "Approval-consumption dry run proves digest, marker-reservation rehearsal, duplicate block, and no execution.",
            ok=dry_run_ready,
            status="VERIFIED / DRY-RUN" if dry_run_ready else "BLOCKED",
            evidence={
                "status": consumption_dry_run.get("status"),
                "marker_reservation_proof_passed": dry_summary.get("marker_reservation_proof_passed"),
                "duplicate_consumption_blocked": dry_summary.get("duplicate_consumption_blocked"),
            },
        ),
        _item(
            "installer_build_execution_readiness_verified",
            "Approved execution proof preflight is ready without execution.",
            ok=readiness_ready,
            status="READY / NO EXECUTION" if readiness_ready else "BLOCKED",
            evidence={
                "status": execution_proof.get("status"),
                "execution_requested": execution_summary.get("execution_requested"),
                "execution_performed": execution_summary.get("execution_performed"),
                "future_output_paths_clear": execution_summary.get("future_output_paths_clear"),
            },
        ),
        _item(
            "installer_build_approved_execution_performed",
            "Approved execution consumes the approval exactly once and writes installer output evidence.",
            ok=approved_execution_performed and installer_outputs_present,
            status="VERIFIED / APPROVAL CONSUMED / PROOF WRITTEN"
            if approved_execution_performed and installer_outputs_present
            else "NOT BUILT / EXPLICIT EXECUTION APPROVAL REQUIRED",
            evidence={
                "approval_consumed": execution_summary.get("approval_consumed"),
                "exact_once_marker": marker_record,
                "output_root": output_root_record,
                "portable_zip": portable_zip_record,
                "build_manifest": manifest_record,
                "execution_evidence": execution_evidence_record,
            },
            blocker=None
            if approved_execution_performed and installer_outputs_present
            else "Run studio-installer-build-approved-execution-proof --execute only after explicit execution approval.",
        ),
        _item(
            "card_ui_inventory_current",
            "Full Desktop/Card UI inventory uses current Pass 10B audit truth and enumerates native panels.",
            ok=card_inventory_current,
            status="VERIFIED / ROADMAP ITEM STILL OPEN" if card_inventory_current else "BLOCKED",
            evidence={
                "status": card_inventory.get("status"),
                "mounted_panels": card_summary.get("live_registry_mounted_panel_count"),
                "approval_gated_panels": card_summary.get("approval_gated_panel_count"),
                "full_desktop_card_ui_closed": card_claim.get("full_desktop_card_ui_closed"),
            },
        ),
        _item(
            "webview2_diagnostics_bounded_historical",
            "Newer WebView2 remediation diagnostics are bounded historical review evidence unless the lane is resumed.",
            ok=webview2_historical,
            status="REVIEW-ONLY / HISTORICAL DIAGNOSTIC" if webview2_historical else "NOT PRESENT",
            evidence=(
                (card_inventory.get("evidence") or {}).get("latest_webview2_operator_remediation_packet")
                or card_sources.get("latest_webview2_operator_remediation_packet")
                or {}
            ),
        ),
        _item(
            "no_forbidden_mutation",
            "Only approved installer-proof marker/output writes are present; host/signing/startup/release/provider/Agent Bus/canonical mutation remains absent.",
            ok=no_forbidden_mutation,
            status="VERIFIED" if no_forbidden_mutation else "BLOCKED",
            evidence={
                "forbidden_authority_clear": forbidden_authority_clear,
                "execution_absent": execution_absent,
                "approved_execution_state_valid": approved_execution_state_valid,
                "marker_exists": marker_record.get("exists"),
                "output_root_exists": output_root_record.get("exists"),
                "portable_zip_exists": portable_zip_record.get("exists"),
            },
        ),
    ]

    required_current_ready = all(row["ok"] for row in checklist if row["id"] != "installer_build_approved_execution_performed")
    complete = bool(required_current_ready and approved_execution_performed and installer_outputs_present)
    status = COMPLETE_STATUS if complete else PARTIAL_STATUS if required_current_ready else BLOCKED_STATUS
    missing_or_unverified = [row["id"] for row in checklist if not row["ok"]]
    verified_but_open = []
    if card_inventory_current and card_claim.get("full_desktop_card_ui_closed") is False:
        verified_but_open.append("card_ui_inventory_current")
    operator_handoff = _operator_execution_handoff(
        approval_packet_id=packet_id,
        ready_for_execution=bool(readiness_ready and required_current_ready),
        approved_execution_performed=approved_execution_performed,
        execution_paths=execution_paths,
    )

    return {
        "ok": complete,
        "complete": complete,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "status": status,
        "generated_at": timestamp,
        "vault_root": str(vault),
        "objective_restated": (
            "Determine whether the Pass 10B expansion pack is actually complete by checking the "
            "current Pass 10B visual proof, installer-build approval artifact, dry-run/readiness proofs, "
            "approved execution marker/output, card UI inventory, and mutation boundaries."
        ),
        "summary": {
            "approval_packet_id": packet_id,
            "current_pass10b_visual_proof_verified": visual_green,
            "approval_artifact_written": approval_ready,
            "consumption_dry_run_verified": dry_run_ready,
            "approved_execution_readiness_verified": readiness_ready,
            "approved_execution_performed": approved_execution_performed,
            "installer_outputs_present": installer_outputs_present,
            "card_ui_inventory_current": card_inventory_current,
            "full_desktop_card_ui_closed": card_claim.get("full_desktop_card_ui_closed"),
            "no_forbidden_mutation_detected": no_forbidden_mutation,
            "next_recommended_pass": NEXT_SIGNING_APPROVAL_PASS if complete else NEXT_EXECUTION_PASS,
        },
        "operator_execution_handoff": operator_handoff,
        "prompt_to_artifact_checklist": checklist,
        "missing_or_unverified": missing_or_unverified,
        "verified_but_open": verified_but_open,
        "evidence": {
            "installer_plan": {
                "ok": installer_plan.get("ok"),
                "status": installer_plan.get("status"),
                "pass10b_completion_audit": pass10b_evidence,
            },
            "approval_review": {
                "ok": approval_review.get("ok"),
                "status": approval_review.get("status"),
                "summary": review_summary,
            },
            "approval_consumption_dry_run": {
                "ok": consumption_dry_run.get("ok"),
                "status": consumption_dry_run.get("status"),
                "summary": dry_summary,
            },
            "approved_execution_proof_readiness": {
                "ok": execution_proof.get("ok"),
                "status": execution_proof.get("status"),
                "summary": execution_summary,
                "paths": execution_paths,
                "preflight_checks": execution_proof.get("preflight_checks") or {},
            },
            "card_ui_inventory": {
                "ok": card_inventory.get("ok"),
                "status": card_inventory.get("status"),
                "summary": card_summary,
                "current_pass10b_completion_audit": (card_inventory.get("evidence") or {}).get(
                    "current_pass10b_completion_audit"
                )
                or card_sources.get("latest_pass10b_completion_audit"),
                "latest_webview2_operator_remediation_packet": (
                    (card_inventory.get("evidence") or {}).get("latest_webview2_operator_remediation_packet")
                    or card_sources.get("latest_webview2_operator_remediation_packet")
                ),
            },
        },
        "authority": {
            "read_only": True,
            "local_only": True,
            "writes_report_only_when_requested": True,
            "consumes_approval_decision": False,
            "reserves_idempotency_marker": False,
            "builds_installer": False,
            "writes_installer": False,
            "signs_artifacts": False,
            "reads_signing_certificate": False,
            "writes_host_startup": False,
            "registers_autostart": False,
            "writes_registry": False,
            "writes_start_menu": False,
            "writes_desktop_shortcut": False,
            "promotes_release": False,
            "writes_release_status": False,
            "launches_pywebview": False,
            "starts_servers": False,
            "launches_executable": False,
            "provider_calls_allowed": False,
            "connector_calls_allowed": False,
            "writes_agent_bus_tasks": False,
            "mutates_gate": False,
            "executes_workflows": False,
            "canonical_mutation_allowed": False,
        },
        "unverified": [
            "Signing, startup/autostart, release publication, and host mutation remain separate deferred gates.",
            "The portable ZIP was not launched or installed by this audit.",
        ]
        if complete
        else [
            "Approved installer-build execution has not run in this audit.",
            "No exact-once marker, portable ZIP, manifest, or execution evidence is present until the approved execution pass runs.",
            "Signing, startup/autostart, release publication, and host mutation remain separate deferred gates.",
        ],
        "next_recommended_pass": NEXT_SIGNING_APPROVAL_PASS if complete else NEXT_EXECUTION_PASS,
    }


def write_pass10b_expansion_pack_completion_audit(
    vault_root: str | Path,
    *,
    approval_packet_id: str | None = None,
    generated_at: str | None = None,
    report_slug: str | None = None,
    output_path: str | Path | None = None,
) -> dict[str, Any]:
    """Write a JSON audit report under a vault-scoped path."""

    vault = _vault_path(vault_root)
    report = build_pass10b_expansion_pack_completion_audit(
        vault,
        approval_packet_id=approval_packet_id,
        generated_at=generated_at,
    )
    if output_path is not None:
        target = _resolve_vault_relative(vault, output_path)
    else:
        slug = report_slug or report["generated_at"].replace(":", "").replace("-", "").split(".")[0].replace("T", "T")
        target = (vault / DEFAULT_REPORT_ROOT / f"{slug}.json").resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    report["written_report"] = _relative_to_vault(vault, target)
    target.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def format_pass10b_operator_execution_handoff(report: dict[str, Any]) -> str:
    """Format the operator execution handoff as reviewable Markdown."""

    summary = report.get("summary") or {}
    handoff = report.get("operator_execution_handoff") or {}
    expected_writes = handoff.get("expected_writes_if_approved") or {}
    checklist = report.get("prompt_to_artifact_checklist") or []
    forbidden = handoff.get("forbidden_even_if_approved") or []
    lines = [
        "---",
        "runtime: Codex",
        "surface: studio_pass10b_expansion_pack_execution_handoff",
        f"generated_at: {report.get('generated_at')}",
        f"status: {handoff.get('status')}",
        f"complete: {report.get('complete')}",
        "---",
        "",
        "# Pass 10B Execution Operator Handoff",
        "",
        "## Current Status",
        "",
        f"- Completion audit status: {report.get('status')}",
        f"- Handoff status: {handoff.get('status')}",
        f"- Approval packet: {summary.get('approval_packet_id')}",
        f"- Approved execution performed: {summary.get('approved_execution_performed')}",
        f"- Installer outputs present: {summary.get('installer_outputs_present')}",
        "",
        "## Explicit Approval Required",
        "",
        handoff.get("approval_statement") or "Explicit operator approval is required before execution.",
        "",
        "## Execution Command",
        "",
        "```powershell",
        handoff.get("execution_command") or "",
        "```",
        "",
        "## Post-Execution Audit Command",
        "",
        "```powershell",
        handoff.get("post_execution_audit_command") or "",
        "```",
        "",
        "## Expected Writes If Approved",
        "",
    ]
    for name, record in expected_writes.items():
        record = record or {}
        lines.append(f"- {name}: `{record.get('path')}` (exists now: {record.get('exists')})")
    lines.extend(["", "## Forbidden Even If Approved", ""])
    for item in forbidden:
        lines.append(f"- {item}")
    lines.extend(["", "## Checklist", ""])
    for row in checklist:
        lines.append(f"- {row.get('id')}: {row.get('status')} (ok: {row.get('ok')})")
    lines.extend(
        [
            "",
            "## Duplicate Policy",
            "",
            handoff.get("duplicate_policy") or "No duplicate policy recorded.",
            "",
            "## Boundary",
            "",
            "This handoff does not execute the installer-build proof, consume approval, reserve a marker, "
            "write installer output, sign artifacts, mutate host/startup/release state, call providers or "
            "connectors, write Agent Bus tasks, mutate Gate/Git/workflow state, or mutate canonical ChaseOS state.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_pass10b_operator_execution_handoff(
    vault_root: str | Path,
    *,
    report: dict[str, Any] | None = None,
    approval_packet_id: str | None = None,
    generated_at: str | None = None,
    report_slug: str | None = None,
    output_path: str | Path | None = None,
) -> dict[str, Any]:
    """Write a Markdown operator handoff under a vault-scoped path."""

    vault = _vault_path(vault_root)
    handoff_report = report or build_pass10b_expansion_pack_completion_audit(
        vault,
        approval_packet_id=approval_packet_id,
        generated_at=generated_at,
    )
    if output_path is not None:
        target = _resolve_vault_relative(vault, output_path)
    else:
        slug = report_slug or handoff_report["generated_at"].replace(":", "").replace("-", "").split(".")[0].replace("T", "T")
        target = (vault / DEFAULT_HANDOFF_ROOT / f"{slug}-operator-handoff.md").resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    content = format_pass10b_operator_execution_handoff(handoff_report)
    handoff_report["written_handoff"] = _relative_to_vault(vault, target)
    handoff_report["written_handoff_sha256"] = hashlib.sha256(content.encode("utf-8")).hexdigest()
    handoff_report["written_handoff_size_bytes"] = len(content.encode("utf-8"))
    target.write_text(content, encoding="utf-8", newline="\n")
    if handoff_report.get("written_report"):
        report_target = _resolve_vault_relative(vault, handoff_report["written_report"])
        report_target.write_text(json.dumps(handoff_report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return handoff_report


def _latest_report_path(vault: Path) -> Path | None:
    root = vault / DEFAULT_REPORT_ROOT
    if not root.exists():
        return None
    reports = [path for path in root.glob("*.json") if path.is_file()]
    if not reports:
        return None
    return max(reports, key=lambda path: (path.stat().st_mtime, path.name))


def build_pass10b_operator_handoff_integrity_verifier(
    vault_root: str | Path,
    *,
    report_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Verify that the JSON audit handoff metadata matches the Markdown handoff file."""

    vault = _vault_path(vault_root)
    timestamp = generated_at or _now_utc()
    selected_report = _resolve_vault_relative(vault, report_path) if report_path else _latest_report_path(vault)
    report_record = _path_record(vault, selected_report)
    payload: dict[str, Any] = {}
    report_error = None
    if selected_report and selected_report.is_file():
        try:
            payload = json.loads(selected_report.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            report_error = f"invalid_json: {exc.msg}"

    handoff_path_value = payload.get("written_handoff")
    handoff_record = _path_record(vault, handoff_path_value)
    expected_sha = payload.get("written_handoff_sha256")
    expected_size = payload.get("written_handoff_size_bytes")
    actual_sha = None
    actual_size = None
    if handoff_path_value and handoff_record.get("exists") and handoff_record.get("is_file"):
        handoff_path = _resolve_vault_relative(vault, handoff_path_value)
        content = handoff_path.read_bytes()
        actual_sha = hashlib.sha256(content).hexdigest()
        actual_size = len(content)

    summary = payload.get("summary") or {}
    handoff = payload.get("operator_execution_handoff") or {}
    digest_matches = bool(expected_sha and actual_sha and expected_sha == actual_sha)
    size_matches = bool(expected_size is not None and actual_size is not None and expected_size == actual_size)
    handoff_ready = handoff.get("status") == "READY_FOR_OPERATOR_APPROVAL"
    no_execution = bool(
        payload.get("complete") is False
        and summary.get("approved_execution_performed") is False
        and summary.get("installer_outputs_present") is False
    )
    ok = bool(
        report_record.get("exists")
        and report_error is None
        and handoff_record.get("exists")
        and digest_matches
        and size_matches
        and handoff_ready
        and no_execution
    )
    blockers = []
    if not report_record.get("exists"):
        blockers.append("report_missing")
    if report_error:
        blockers.append(report_error)
    if not handoff_record.get("exists"):
        blockers.append("handoff_missing")
    if not digest_matches:
        blockers.append("handoff_sha256_mismatch")
    if not size_matches:
        blockers.append("handoff_size_mismatch")
    if not handoff_ready:
        blockers.append("handoff_not_ready_for_operator_approval")
    if not no_execution:
        blockers.append("execution_or_output_already_present")

    return {
        "ok": ok,
        "surface": "studio_pass10b_operator_handoff_integrity_verifier",
        "model_version": MODEL_VERSION,
        "status": HANDOFF_INTEGRITY_STATUS if ok else HANDOFF_INTEGRITY_BLOCKED_STATUS,
        "generated_at": timestamp,
        "vault_root": str(vault),
        "report": report_record,
        "handoff": handoff_record,
        "summary": {
            "report_path": report_record.get("path"),
            "handoff_path": handoff_record.get("path"),
            "expected_sha256": expected_sha,
            "actual_sha256": actual_sha,
            "expected_size_bytes": expected_size,
            "actual_size_bytes": actual_size,
            "digest_matches": digest_matches,
            "size_matches": size_matches,
            "handoff_ready_for_operator_approval": handoff_ready,
            "approved_execution_performed": summary.get("approved_execution_performed"),
            "installer_outputs_present": summary.get("installer_outputs_present"),
            "no_execution": no_execution,
            "next_recommended_pass": NEXT_EXECUTION_PASS,
        },
        "blockers": blockers,
        "authority": {
            "read_only": True,
            "local_only": True,
            "writes_report": False,
            "writes_handoff": False,
            "consumes_approval_decision": False,
            "reserves_idempotency_marker": False,
            "builds_installer": False,
            "writes_installer": False,
            "launches_executable": False,
            "starts_servers": False,
            "provider_calls_allowed": False,
            "connector_calls_allowed": False,
            "writes_agent_bus_tasks": False,
            "mutates_gate": False,
            "executes_workflows": False,
            "canonical_mutation_allowed": False,
        },
        "next_recommended_pass": NEXT_EXECUTION_PASS,
    }


def format_pass10b_operator_handoff_integrity_verifier(report: dict[str, Any]) -> str:
    summary = report.get("summary") or {}
    lines = [
        "Pass 10B operator handoff integrity verifier",
        f"  status: {report.get('status')}",
        f"  ok: {report.get('ok')}",
        f"  report: {summary.get('report_path')}",
        f"  handoff: {summary.get('handoff_path')}",
        f"  digest_matches: {summary.get('digest_matches')}",
        f"  size_matches: {summary.get('size_matches')}",
        f"  handoff_ready_for_operator_approval: {summary.get('handoff_ready_for_operator_approval')}",
        f"  no_execution: {summary.get('no_execution')}",
        f"  next: {report.get('next_recommended_pass')}",
    ]
    blockers = report.get("blockers") or []
    if blockers:
        lines.append(f"  blockers: {', '.join(str(blocker) for blocker in blockers)}")
    return "\n".join(lines)


def format_pass10b_expansion_pack_completion_audit(report: dict[str, Any]) -> str:
    summary = report.get("summary") or {}
    handoff = report.get("operator_execution_handoff") or {}
    lines = [
        "Pass 10B expansion-pack completion audit",
        f"  status: {report.get('status')}",
        f"  complete: {report.get('complete')}",
        f"  pass10b_visual_proof_verified: {summary.get('current_pass10b_visual_proof_verified')}",
        f"  approval_artifact_written: {summary.get('approval_artifact_written')}",
        f"  consumption_dry_run_verified: {summary.get('consumption_dry_run_verified')}",
        f"  approved_execution_readiness_verified: {summary.get('approved_execution_readiness_verified')}",
        f"  approved_execution_performed: {summary.get('approved_execution_performed')}",
        f"  installer_outputs_present: {summary.get('installer_outputs_present')}",
        f"  card_ui_inventory_current: {summary.get('card_ui_inventory_current')}",
        f"  no_forbidden_mutation_detected: {summary.get('no_forbidden_mutation_detected')}",
        f"  handoff_status: {handoff.get('status')}",
        f"  execution_command: {handoff.get('execution_command')}",
        f"  next: {report.get('next_recommended_pass')}",
    ]
    if report.get("written_report"):
        lines.append(f"  report: {report.get('written_report')}")
    if report.get("written_handoff"):
        lines.append(f"  handoff: {report.get('written_handoff')}")
    if report.get("written_handoff_sha256"):
        lines.append(f"  handoff_sha256: {report.get('written_handoff_sha256')}")
    if report.get("written_handoff_size_bytes") is not None:
        lines.append(f"  handoff_size_bytes: {report.get('written_handoff_size_bytes')}")
    return "\n".join(lines)
