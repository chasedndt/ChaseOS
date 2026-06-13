"""Studio MVP operator decision packet and closure gate.

This surface follows the deferral closeout audit by recording a bounded
operator decision profile. It can acknowledge an internal portable MVP profile,
defer nonessential/high-risk lanes, and leave manual install/launch acceptance
as the remaining gate. It does not execute any deferred lane.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from runtime.studio.studio_mvp_deferral_closeout_audit import (
    build_studio_mvp_deferral_closeout_audit,
)


MODEL_VERSION = "studio.mvp_operator_decision.v1"
DECISION_SURFACE_ID = "studio_mvp_operator_decision_packet"
CLOSURE_SURFACE_ID = "studio_mvp_closure_gate"
PASS_ID = "studio-mvp-operator-governed-executor-deferred-closeout"
DEFAULT_DECISION_ROOT = Path("07_LOGS") / "Studio-Graph-Views" / "studio-mvp-operator-decisions"
DEFAULT_CLOSURE_ROOT = Path("07_LOGS") / "Studio-Graph-Views" / "studio-mvp-closure-gates"
INTERNAL_PORTABLE_PROFILE = "internal-portable-mvp"
NEXT_RECOMMENDED_PASS = "studio-mvp-manual-install-launch-acceptance"


DEFERRED_FOR_INTERNAL_PORTABLE_MVP = {
    "branded_installer_logo_icon",
    "signing_chain",
    "startup_autostart_host_mutation",
    "release_promotion",
    "real_target_workspace_migration",
    "provider_model_live_calls",
    "runtime_dispatch_activation",
    "browser_dispatch_activation",
    "companion_selection_executor",
    "persisted_graph_storage_durable_ids",
}


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _safe_slug(value: str | None) -> str:
    raw = value or datetime.now(timezone.utc).strftime("%Y-%m-%d-studio-mvp-operator-decision")
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", raw.strip()).strip(".-")
    return slug or "studio-mvp-operator-decision"


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


def _resolve_inside_vault(vault: Path, path_value: str | Path, *, label: str) -> Path:
    path = Path(path_value)
    resolved = path.resolve() if path.is_absolute() else (vault / path).resolve()
    try:
        resolved.relative_to(vault.resolve())
    except ValueError as exc:
        raise ValueError(f"{label} must stay inside the vault workspace: {path_value}") from exc
    return resolved


def _resolve_root(vault: Path, root: str | Path | None, default_root: Path, *, label: str) -> Path:
    root_input = Path(root) if root else default_root
    return _resolve_inside_vault(vault, root_input, label=label)


def _path_record(vault: Path, path_value: str | Path | None) -> dict[str, Any]:
    if not path_value:
        return {"path": None, "exists": False, "is_file": False, "inside_vault": None}
    try:
        path = _resolve_inside_vault(vault, path_value, label="manual acceptance evidence")
    except ValueError:
        return {"path": str(path_value), "exists": False, "is_file": False, "inside_vault": False}
    return {
        "path": _relative_to_vault(vault, path),
        "exists": path.exists(),
        "is_file": path.is_file(),
        "inside_vault": True,
        "size_bytes": path.stat().st_size if path.is_file() else 0,
    }


def _authority() -> dict[str, Any]:
    return {
        "read_only_until_write_flag": True,
        "decision_packet_write_allowed_when_requested": True,
        "closure_report_write_allowed_when_requested": True,
        "approval_queue_write_allowed": False,
        "approval_consumption_allowed": False,
        "approval_execution_allowed": False,
        "signing_allowed": False,
        "reads_credentials_or_secrets": False,
        "provider_calls_allowed": False,
        "model_calls_allowed": False,
        "runtime_dispatch_allowed": False,
        "browser_control_allowed": False,
        "app_launch_allowed": False,
        "host_mutation_allowed": False,
        "target_mutation_allowed": False,
        "release_promotion_allowed": False,
        "agent_bus_task_write_allowed": False,
        "canonical_mutation_allowed": False,
    }


def _decision_for_item(
    item: dict[str, Any],
    *,
    deferrals_acknowledged: bool,
    manual_acceptance_status: str,
    manual_acceptance_evidence: dict[str, Any],
) -> dict[str, Any]:
    item_id = item["id"]
    if item_id == "pass10b_installer_zip_proof":
        decision = "accepted_existing_evidence"
        status = "COMPLETE / ACCEPTED AS INTERNAL PORTABLE MVP BASELINE"
    elif item_id == "real_install_launch_manual_test":
        decision = "selected_for_manual_acceptance"
        if manual_acceptance_status == "accepted" and manual_acceptance_evidence.get("exists"):
            status = "COMPLETE / OPERATOR MANUAL ACCEPTANCE EVIDENCE PRESENT"
        else:
            status = "OPEN / REQUIRED FOR INTERNAL PORTABLE MVP ACCEPTANCE"
    elif item_id in DEFERRED_FOR_INTERNAL_PORTABLE_MVP:
        decision = "deferred_for_internal_portable_mvp"
        status = "DEFERRED / OPERATOR ACKNOWLEDGED" if deferrals_acknowledged else "READY_FOR_DEFERRAL / OPERATOR_ACK_REQUIRED"
    else:
        decision = "unclassified"
        status = "BLOCKED / DECISION_RULE_MISSING"
    return {
        "id": item_id,
        "title": item.get("title"),
        "source_status": item.get("status"),
        "decision": decision,
        "decision_status": status,
        "operator_required": item.get("operator_required"),
        "operator_input_types": item.get("operator_input_types") or [],
        "deferral_requirement": item.get("deferral_requirement"),
        "next_governed_surface": item.get("next_governed_surface"),
    }


def _decision_digest(payload: dict[str, Any]) -> str:
    selected = {
        "surface": payload.get("surface"),
        "profile": payload.get("profile"),
        "operator_id": payload.get("operator_id"),
        "operator_deferrals_acknowledged": (payload.get("summary") or {}).get("operator_deferrals_acknowledged"),
        "manual_acceptance_status": (payload.get("summary") or {}).get("manual_acceptance_status"),
        "decisions": [
            {
                "id": item.get("id"),
                "decision": item.get("decision"),
                "decision_status": item.get("decision_status"),
            }
            for item in payload.get("decisions", [])
        ],
    }
    blob = json.dumps(selected, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def _write_json_markdown(
    *,
    vault: Path,
    payload: dict[str, Any],
    root: str | Path | None,
    default_root: Path,
    slug: str | None,
    formatter,
    label: str,
) -> dict[str, Any]:
    target_root = _resolve_root(vault, root, default_root, label=label)
    target_root.mkdir(parents=True, exist_ok=True)
    safe_slug = _safe_slug(slug)
    json_path = target_root / f"{safe_slug}.json"
    markdown_path = target_root / f"{safe_slug}.md"
    evidence = {
        "written": True,
        "json_path": _relative_to_vault(vault, json_path),
        "markdown_path": _relative_to_vault(vault, markdown_path),
    }
    payload["evidence"] = evidence
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_path.write_text(formatter(payload) + "\n", encoding="utf-8")
    return evidence


def build_studio_mvp_operator_decision_packet(
    vault_root: str | Path,
    *,
    profile: str = INTERNAL_PORTABLE_PROFILE,
    operator_id: str = "operator",
    decision_note: str | None = None,
    acknowledge_preapproved_deferrals: bool = False,
    manual_acceptance_status: str = "not_performed",
    manual_acceptance_evidence_path: str | Path | None = None,
    write_decision: bool = False,
    decision_root: str | Path | None = None,
    decision_slug: str | None = None,
) -> dict[str, Any]:
    """Build an operator decision packet from the current MVP deferral audit."""

    if profile != INTERNAL_PORTABLE_PROFILE:
        raise ValueError(f"unsupported Studio MVP decision profile: {profile}")
    if manual_acceptance_status not in {"not_performed", "accepted", "deferred"}:
        raise ValueError("manual acceptance status must be one of: not_performed, accepted, deferred")

    vault = _vault_path(vault_root)
    closeout = build_studio_mvp_deferral_closeout_audit(vault)
    items = closeout.get("operator_human_in_loop_matrix") or []
    manual_evidence = _path_record(vault, manual_acceptance_evidence_path)
    decisions = [
        _decision_for_item(
            item,
            deferrals_acknowledged=acknowledge_preapproved_deferrals,
            manual_acceptance_status=manual_acceptance_status,
            manual_acceptance_evidence=manual_evidence,
        )
        for item in items
    ]
    deferred_decisions = [item for item in decisions if item["decision"] == "deferred_for_internal_portable_mvp"]
    open_required = [
        item
        for item in decisions
        if item["decision"] == "selected_for_manual_acceptance"
        and not (
            manual_acceptance_status == "accepted"
            and manual_evidence.get("exists") is True
            and manual_evidence.get("inside_vault") is True
        )
    ]
    deferrals_complete = bool(deferred_decisions) and all(
        item["decision_status"] == "DEFERRED / OPERATOR ACKNOWLEDGED" for item in deferred_decisions
    )
    manual_acceptance_complete = not open_required
    mvp_closed = bool(closeout.get("summary", {}).get("pass10b_installer_zip_proof_complete")) and deferrals_complete and manual_acceptance_complete
    candidate_status = (
        "COMPLETE / INTERNAL PORTABLE MVP CLOSED WITH DEFERRALS"
        if mvp_closed
        else "PARTIAL / INTERNAL PORTABLE MVP CANDIDATE / MANUAL ACCEPTANCE REQUIRED"
        if deferrals_complete
        else "DRAFT / OPERATOR DEFERRAL ACKNOWLEDGEMENT REQUIRED"
    )

    packet: dict[str, Any] = {
        "ok": True,
        "closed": mvp_closed,
        "surface": DECISION_SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": candidate_status,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "profile": profile,
        "operator_id": operator_id,
        "decision_note": decision_note,
        "objective_restated": (
            "Record the operator-governed MVP decision profile that accepts the verified Pass 10B ZIP proof, "
            "defers nonessential/high-risk lanes for an internal portable MVP, and keeps real install/launch acceptance as the remaining gate."
        ),
        "summary": {
            "mvp_closed": mvp_closed,
            "candidate_status": candidate_status,
            "profile": profile,
            "pass10b_installer_zip_proof_complete": closeout.get("summary", {}).get("pass10b_installer_zip_proof_complete"),
            "operator_deferrals_acknowledged": acknowledge_preapproved_deferrals,
            "deferred_for_internal_portable_mvp_count": len(deferred_decisions),
            "manual_acceptance_status": manual_acceptance_status,
            "manual_acceptance_complete": manual_acceptance_complete,
            "remaining_required_count": len(open_required),
            "remaining_required_items": [item["id"] for item in open_required],
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        },
        "manual_acceptance_evidence": manual_evidence,
        "decisions": decisions,
        "source_closeout_summary": closeout.get("summary"),
        "authority": _authority(),
        "must_not_be_auto_run": closeout.get("must_not_be_auto_run"),
        "evidence": {"written": False, "json_path": None, "markdown_path": None},
        "next_recommended_pass": NEXT_RECOMMENDED_PASS,
    }
    packet["decision_digest_sha256"] = _decision_digest(packet)

    if write_decision:
        if not acknowledge_preapproved_deferrals:
            raise ValueError("writing an MVP decision packet requires --acknowledge-preapproved-deferrals")
        _write_json_markdown(
            vault=vault,
            payload=packet,
            root=decision_root,
            default_root=DEFAULT_DECISION_ROOT,
            slug=decision_slug,
            formatter=format_studio_mvp_operator_decision_packet,
            label="Studio MVP operator decision root",
        )
    return packet


def _latest_json(root: Path) -> Path | None:
    if not root.is_dir():
        return None
    candidates = [path for path in root.glob("*.json") if path.is_file()]
    if not candidates:
        return None
    return max(candidates, key=lambda path: (path.stat().st_mtime, path.name))


def _load_decision(vault: Path, decision_path: str | Path | None) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    if decision_path:
        path = _resolve_inside_vault(vault, decision_path, label="Studio MVP decision path")
    else:
        path = _latest_json(_resolve_root(vault, None, DEFAULT_DECISION_ROOT, label="Studio MVP operator decision root"))
    record = _path_record(vault, path) if path else {"path": None, "exists": False, "is_file": False, "inside_vault": True}
    if not path or not path.is_file():
        return None, record
    try:
        return json.loads(path.read_text(encoding="utf-8")), record
    except json.JSONDecodeError as exc:
        record["json_error"] = exc.msg
        return None, record


def build_studio_mvp_closure_gate(
    vault_root: str | Path,
    *,
    decision_path: str | Path | None = None,
    write_report: bool = False,
    report_root: str | Path | None = None,
    report_slug: str | None = None,
) -> dict[str, Any]:
    """Evaluate whether the internal portable MVP can be called closed."""

    vault = _vault_path(vault_root)
    decision, decision_record = _load_decision(vault, decision_path)
    closeout = build_studio_mvp_deferral_closeout_audit(vault)
    blockers: list[str] = []
    if decision is None:
        blockers.append("decision_packet_missing_or_invalid")

    summary = (decision or {}).get("summary") or {}
    if decision and summary.get("operator_deferrals_acknowledged") is not True:
        blockers.append("operator_deferrals_not_acknowledged")
    if decision and summary.get("manual_acceptance_complete") is not True:
        blockers.append("manual_install_launch_acceptance_missing")
    manual_acceptance_evidence_validation: dict[str, Any] | None = None
    if decision and summary.get("manual_acceptance_complete") is True:
        try:
            from runtime.studio.studio_mvp_manual_acceptance import (
                validate_studio_mvp_manual_acceptance_evidence,
            )

            evidence_path = ((decision or {}).get("manual_acceptance_evidence") or {}).get("path")
            manual_acceptance_evidence_validation = validate_studio_mvp_manual_acceptance_evidence(
                vault,
                evidence_path,
            )
        except (ImportError, ValueError):
            manual_acceptance_evidence_validation = {"valid": False}
        if not manual_acceptance_evidence_validation.get("valid"):
            blockers.append("manual_acceptance_evidence_invalid")
    if closeout.get("summary", {}).get("pass10b_installer_zip_proof_complete") is not True:
        blockers.append("pass10b_installer_zip_proof_not_complete")

    closed = len(blockers) == 0
    status = (
        "COMPLETE / INTERNAL PORTABLE MVP CLOSED WITH DEFERRALS"
        if closed
        else "PARTIAL / INTERNAL PORTABLE MVP CANDIDATE / MANUAL ACCEPTANCE REQUIRED"
        if decision and summary.get("operator_deferrals_acknowledged") is True
        else "BLOCKED / OPERATOR DECISION PACKET REQUIRED"
    )
    report: dict[str, Any] = {
        "ok": True,
        "closed": closed,
        "surface": CLOSURE_SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": status,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "summary": {
            "mvp_closed": closed,
            "closure_status": status,
            "decision_packet_present": decision is not None,
            "operator_deferrals_acknowledged": summary.get("operator_deferrals_acknowledged"),
            "manual_acceptance_complete": summary.get("manual_acceptance_complete"),
            "pass10b_installer_zip_proof_complete": closeout.get("summary", {}).get("pass10b_installer_zip_proof_complete"),
            "blocker_count": len(blockers),
            "next_recommended_pass": None if closed else NEXT_RECOMMENDED_PASS,
        },
        "blockers": blockers,
        "decision_record": decision_record,
        "decision_summary": summary,
        "manual_acceptance_evidence_validation": manual_acceptance_evidence_validation,
        "authority": _authority(),
        "evidence": {"written": False, "json_path": None, "markdown_path": None},
        "next_recommended_pass": None if closed else NEXT_RECOMMENDED_PASS,
    }
    if write_report:
        _write_json_markdown(
            vault=vault,
            payload=report,
            root=report_root,
            default_root=DEFAULT_CLOSURE_ROOT,
            slug=report_slug,
            formatter=format_studio_mvp_closure_gate,
            label="Studio MVP closure gate report root",
        )
    return report


def format_studio_mvp_operator_decision_packet(packet: dict[str, Any]) -> str:
    summary = packet.get("summary") or {}
    lines = [
        "Studio MVP Operator Decision Packet",
        f"  status: {packet.get('status')}",
        f"  profile: {packet.get('profile')}",
        f"  mvp_closed: {summary.get('mvp_closed')}",
        f"  pass10b_installer_zip_proof_complete: {summary.get('pass10b_installer_zip_proof_complete')}",
        f"  operator_deferrals_acknowledged: {summary.get('operator_deferrals_acknowledged')}",
        f"  deferred_for_internal_portable_mvp_count: {summary.get('deferred_for_internal_portable_mvp_count')}",
        f"  manual_acceptance_status: {summary.get('manual_acceptance_status')}",
        f"  remaining_required_items: {', '.join(summary.get('remaining_required_items') or [])}",
        f"  decision_digest_sha256: {packet.get('decision_digest_sha256')}",
        f"  next: {summary.get('next_recommended_pass')}",
        "",
        "Decisions:",
    ]
    for item in packet.get("decisions") or []:
        lines.append(f"- {item.get('id')}: {item.get('decision')} ({item.get('decision_status')})")
    lines.append("")
    lines.append(
        "Boundary: decision/report packet only; no approval consumption/execution, signing, secret reads, provider/model call, runtime/browser dispatch, app launch, host mutation, target mutation, release promotion, Agent Bus write, or canonical writeback."
    )
    evidence = packet.get("evidence") or {}
    if evidence.get("written"):
        lines.append(f"Evidence: {evidence.get('markdown_path')}")
    return "\n".join(lines)


def format_studio_mvp_closure_gate(report: dict[str, Any]) -> str:
    summary = report.get("summary") or {}
    lines = [
        "Studio MVP Closure Gate",
        f"  status: {report.get('status')}",
        f"  mvp_closed: {summary.get('mvp_closed')}",
        f"  decision_packet_present: {summary.get('decision_packet_present')}",
        f"  operator_deferrals_acknowledged: {summary.get('operator_deferrals_acknowledged')}",
        f"  manual_acceptance_complete: {summary.get('manual_acceptance_complete')}",
        f"  pass10b_installer_zip_proof_complete: {summary.get('pass10b_installer_zip_proof_complete')}",
        f"  blockers: {', '.join(report.get('blockers') or [])}",
        f"  next: {summary.get('next_recommended_pass')}",
        "",
        "Boundary: closure report only; no execution or mutation.",
    ]
    evidence = report.get("evidence") or {}
    if evidence.get("written"):
        lines.append(f"Evidence: {evidence.get('markdown_path')}")
    return "\n".join(lines)
