"""Studio MVP manual install/launch acceptance intake.

This surface validates existing packaged launch/visual QA evidence and records
whether the operator accepts that evidence as sufficient for the internal
portable MVP. It does not launch the app, sign artifacts, mutate host state,
call providers, dispatch runtimes, control browsers, or write canonical state.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from runtime.studio.studio_mvp_operator_decision import (
    DEFAULT_DECISION_ROOT,
    build_studio_mvp_closure_gate,
    build_studio_mvp_deferral_closeout_audit,
)


MODEL_VERSION = "studio.mvp_manual_acceptance.v1"
SURFACE_ID = "studio_mvp_manual_install_launch_acceptance"
PASS_ID = "studio-mvp-manual-install-launch-acceptance"
DEFAULT_ACCEPTANCE_ROOT = Path("07_LOGS") / "Studio-Graph-Views" / "studio-mvp-manual-acceptance"
DEFAULT_VISUAL_QA_PATH = Path("07_LOGS") / "Studio-Graph-Views" / "2026-05-11-studio-pass10b-final-current-visual-qa-v2.json"
NEXT_RECOMMENDED_PASS_IF_READY = "operator-provide-manual-acceptance-statement"
NEXT_RECOMMENDED_PASS_IF_ACCEPTED = "studio-mvp-close-internal-portable-profile"


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _safe_slug(value: str | None) -> str:
    raw = value or datetime.now(timezone.utc).strftime("%Y-%m-%d-studio-mvp-manual-acceptance")
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", raw.strip()).strip(".-")
    return slug or "studio-mvp-manual-acceptance"


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
    if path.is_absolute():
        resolved = path.resolve()
    else:
        cwd_resolved = path.resolve()
        try:
            cwd_resolved.relative_to(vault.resolve())
            resolved = cwd_resolved
        except ValueError:
            resolved = (vault / path).resolve()
    try:
        resolved.relative_to(vault.resolve())
    except ValueError as exc:
        raise ValueError(f"{label} must stay inside the vault workspace: {path_value}") from exc
    return resolved


def _path_record(vault: Path, path_value: str | Path | None, *, label: str = "path") -> dict[str, Any]:
    if not path_value:
        return {"path": None, "exists": False, "is_file": False, "inside_vault": None}
    try:
        path = _resolve_inside_vault(vault, path_value, label=label)
    except ValueError:
        return {"path": str(path_value), "exists": False, "is_file": False, "inside_vault": False}
    return {
        "path": _relative_to_vault(vault, path),
        "exists": path.exists(),
        "is_file": path.is_file(),
        "inside_vault": True,
        "size_bytes": path.stat().st_size if path.is_file() else 0,
    }


def _latest_json(root: Path) -> Path | None:
    if not root.is_dir():
        return None
    candidates = [path for path in root.glob("*.json") if path.is_file()]
    if not candidates:
        return None
    return max(candidates, key=lambda path: (path.stat().st_mtime, path.name))


def _load_json(vault: Path, path_value: str | Path | None, *, default_path: Path | None, label: str) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    path = _resolve_inside_vault(vault, path_value or default_path, label=label) if path_value or default_path else None
    record = _path_record(vault, path, label=label) if path else {"path": None, "exists": False, "is_file": False, "inside_vault": True}
    if not path or not path.is_file():
        return None, record
    try:
        return json.loads(path.read_text(encoding="utf-8")), record
    except json.JSONDecodeError as exc:
        record["json_error"] = exc.msg
        return None, record


def _load_latest_decision(vault: Path, decision_path: str | Path | None) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    default = _latest_json(_resolve_inside_vault(vault, DEFAULT_DECISION_ROOT, label="Studio MVP decision root"))
    return _load_json(vault, decision_path, default_path=default, label="Studio MVP decision packet")


def _visual_qa_checks(vault: Path, visual_qa_path: str | Path | None) -> dict[str, Any]:
    payload, record = _load_json(vault, visual_qa_path, default_path=DEFAULT_VISUAL_QA_PATH, label="packaged visual QA evidence")
    screenshot = (payload or {}).get("screenshot") or {}
    visual = screenshot.get("visual_verification") or {}
    launch = (payload or {}).get("launch") or {}
    termination = (payload or {}).get("termination") or {}
    authority = (payload or {}).get("authority") or {}
    checks = {
        "visual_qa_record_present": record.get("exists") is True and record.get("is_file") is True,
        "visual_qa_ok": bool((payload or {}).get("ok")),
        "visual_qa_status_complete": (payload or {}).get("status") == "packaged_app_visual_qa_complete",
        "launch_started": launch.get("started") is True,
        "process_alive_before_capture": launch.get("process_alive_before_capture") is True,
        "screenshot_exists": screenshot.get("exists") is True,
        "screenshot_nonblank": visual.get("ok") is True and visual.get("reason") == "nonblank",
        "owned_process_terminated": termination.get("terminated") is True,
        "no_forbidden_authority": all(
            authority.get(key) is False
            for key in [
                "writes_installer",
                "writes_host_startup",
                "mutates_gate",
                "grants_approvals",
                "executes_approval_decisions",
                "executes_workflows",
                "provider_calls_allowed",
                "connector_calls_allowed",
                "writes_agent_bus_tasks",
                "canonical_mutation_allowed",
            ]
        ),
    }
    return {
        "record": record,
        "ok": all(checks.values()),
        "checks": checks,
        "summary": {
            "status": (payload or {}).get("status"),
            "executable": (payload or {}).get("executable"),
            "screenshot_path": screenshot.get("path"),
            "screenshot_size_bytes": screenshot.get("size_bytes"),
            "window_title": (screenshot.get("capture") or {}).get("window_title"),
            "unique_color_count": visual.get("unique_color_count"),
            "dominant_color_ratio": visual.get("dominant_color_ratio"),
        },
    }


def _authority() -> dict[str, Any]:
    return {
        "read_only_until_write_flag": True,
        "acceptance_record_write_allowed_when_requested": True,
        "launches_packaged_executable": False,
        "captures_native_screenshot": False,
        "approval_queue_write_allowed": False,
        "approval_consumption_allowed": False,
        "approval_execution_allowed": False,
        "signing_allowed": False,
        "reads_credentials_or_secrets": False,
        "provider_calls_allowed": False,
        "model_calls_allowed": False,
        "runtime_dispatch_allowed": False,
        "browser_control_allowed": False,
        "host_mutation_allowed": False,
        "target_mutation_allowed": False,
        "release_promotion_allowed": False,
        "agent_bus_task_write_allowed": False,
        "canonical_mutation_allowed": False,
    }


def _acceptance_digest(report: dict[str, Any]) -> str:
    selected = {
        "surface": report.get("surface"),
        "operator_id": report.get("operator_id"),
        "accept_existing_automated_evidence": report.get("accept_existing_automated_evidence"),
        "operator_acceptance_statement": report.get("operator_acceptance_statement"),
        "visual_qa_record": ((report.get("automated_evidence") or {}).get("record") or {}).get("path"),
        "accepted": (report.get("summary") or {}).get("manual_acceptance_complete"),
    }
    return hashlib.sha256(json.dumps(selected, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _resolve_acceptance_root(vault: Path, root: str | Path | None) -> Path:
    return _resolve_inside_vault(vault, Path(root) if root else DEFAULT_ACCEPTANCE_ROOT, label="Studio MVP manual acceptance root")


def _write_acceptance(
    *,
    vault: Path,
    report: dict[str, Any],
    acceptance_root: str | Path | None,
    acceptance_slug: str | None,
) -> dict[str, Any]:
    root = _resolve_acceptance_root(vault, acceptance_root)
    root.mkdir(parents=True, exist_ok=True)
    slug = _safe_slug(acceptance_slug)
    json_path = root / f"{slug}.json"
    markdown_path = root / f"{slug}.md"
    evidence = {
        "written": True,
        "json_path": _relative_to_vault(vault, json_path),
        "markdown_path": _relative_to_vault(vault, markdown_path),
    }
    report["evidence"] = evidence
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_path.write_text(format_studio_mvp_manual_acceptance(report) + "\n", encoding="utf-8")
    return evidence


def build_studio_mvp_manual_acceptance(
    vault_root: str | Path,
    *,
    decision_path: str | Path | None = None,
    automated_visual_qa_path: str | Path | None = None,
    operator_id: str = "operator",
    operator_acceptance_statement: str | None = None,
    accept_existing_automated_evidence: bool = False,
    write_acceptance: bool = False,
    acceptance_root: str | Path | None = None,
    acceptance_slug: str | None = None,
) -> dict[str, Any]:
    """Build or write a Studio MVP manual acceptance record."""

    vault = _vault_path(vault_root)
    decision, decision_record = _load_latest_decision(vault, decision_path)
    visual = _visual_qa_checks(vault, automated_visual_qa_path)
    closure = build_studio_mvp_closure_gate(vault, decision_path=decision_record.get("path"))
    statement = (operator_acceptance_statement or "").strip()
    statement_present = len(statement) >= 12
    accepted = bool(accept_existing_automated_evidence and statement_present and visual["ok"])
    blockers: list[str] = []
    if not decision:
        blockers.append("operator_decision_packet_missing")
    if not visual["ok"]:
        blockers.append("automated_visual_qa_evidence_invalid")
    if not accept_existing_automated_evidence:
        blockers.append("operator_has_not_accepted_existing_automated_evidence")
    if not statement_present:
        blockers.append("operator_acceptance_statement_missing")
    status = (
        "COMPLETE / MANUAL ACCEPTANCE RECORDED"
        if accepted
        else "READY / OPERATOR ACCEPTANCE STATEMENT REQUIRED"
        if visual["ok"] and decision
        else "BLOCKED / ACCEPTANCE PREREQUISITES INCOMPLETE"
    )
    report: dict[str, Any] = {
        "ok": True,
        "accepted": accepted,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": status,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "operator_id": operator_id,
        "operator_acceptance_statement": statement or None,
        "accept_existing_automated_evidence": bool(accept_existing_automated_evidence),
        "summary": {
            "manual_acceptance_complete": accepted,
            "automated_visual_qa_valid": visual["ok"],
            "operator_decision_packet_present": decision is not None,
            "operator_acceptance_statement_present": statement_present,
            "blocker_count": len(blockers),
            "next_recommended_pass": NEXT_RECOMMENDED_PASS_IF_ACCEPTED if accepted else NEXT_RECOMMENDED_PASS_IF_READY,
        },
        "blockers": blockers,
        "operator_decision_record": decision_record,
        "operator_decision_summary": (decision or {}).get("summary") or {},
        "current_closure_gate_summary": closure.get("summary"),
        "automated_evidence": visual,
        "authority": _authority(),
        "evidence": {"written": False, "json_path": None, "markdown_path": None},
        "next_recommended_pass": NEXT_RECOMMENDED_PASS_IF_ACCEPTED if accepted else NEXT_RECOMMENDED_PASS_IF_READY,
    }
    report["acceptance_digest_sha256"] = _acceptance_digest(report)
    if write_acceptance:
        _write_acceptance(
            vault=vault,
            report=report,
            acceptance_root=acceptance_root,
            acceptance_slug=acceptance_slug,
        )
    return report


def validate_studio_mvp_manual_acceptance_evidence(vault_root: str | Path, path_value: str | Path | None) -> dict[str, Any]:
    """Validate a manual acceptance record path for closure-gate use."""

    vault = _vault_path(vault_root)
    payload, record = _load_json(vault, path_value, default_path=None, label="Studio MVP manual acceptance evidence")
    valid = (
        payload is not None
        and payload.get("surface") == SURFACE_ID
        and payload.get("accepted") is True
        and (payload.get("summary") or {}).get("manual_acceptance_complete") is True
        and ((payload.get("automated_evidence") or {}).get("ok") is True)
        and bool(payload.get("operator_acceptance_statement"))
    )
    return {
        "valid": bool(valid),
        "record": record,
        "surface": (payload or {}).get("surface"),
        "accepted": (payload or {}).get("accepted"),
        "summary": (payload or {}).get("summary") or {},
    }


def format_studio_mvp_manual_acceptance(report: dict[str, Any]) -> str:
    summary = report.get("summary") or {}
    visual = report.get("automated_evidence") or {}
    lines = [
        "Studio MVP Manual Install/Launch Acceptance",
        f"  status: {report.get('status')}",
        f"  accepted: {report.get('accepted')}",
        f"  automated_visual_qa_valid: {summary.get('automated_visual_qa_valid')}",
        f"  operator_decision_packet_present: {summary.get('operator_decision_packet_present')}",
        f"  operator_acceptance_statement_present: {summary.get('operator_acceptance_statement_present')}",
        f"  visual_qa_record: {((visual.get('record') or {}).get('path'))}",
        f"  screenshot: {((visual.get('summary') or {}).get('screenshot_path'))}",
        f"  acceptance_digest_sha256: {report.get('acceptance_digest_sha256')}",
        f"  next: {summary.get('next_recommended_pass')}",
        "",
        "Blockers:",
        *[f"- {item}" for item in report.get("blockers") or []],
        "",
        "Boundary: acceptance intake only; no app launch, screenshot capture, signing, secret reads, approval consumption/execution, provider/model call, runtime/browser dispatch, host mutation, target mutation, release promotion, Agent Bus write, or canonical writeback.",
    ]
    evidence = report.get("evidence") or {}
    if evidence.get("written"):
        lines.append(f"Evidence: {evidence.get('markdown_path')}")
    return "\n".join(lines)
