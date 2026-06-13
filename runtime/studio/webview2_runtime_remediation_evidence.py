"""Review-only intake for operator WebView2 runtime remediation evidence."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from runtime.studio.packaged_app_launch_smoke import _relative_to_vault


MODEL_VERSION = "studio.webview2_runtime_remediation_evidence.v1"
SURFACE_ID = "studio_webview2_runtime_remediation_evidence"
DEFAULT_REPORT_ROOT = Path("07_LOGS") / "Studio-Graph-Views" / "webview2-runtime-remediation-evidence"
ALLOWED_REMEDIATION_STATUSES = {"performed", "not_performed", "unknown"}


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _resolve_report_root(vault: Path, report_root: str | Path | None) -> Path:
    root = Path(report_root) if report_root else DEFAULT_REPORT_ROOT
    if not root.is_absolute():
        root = vault / root
    root = root.resolve()
    try:
        root.relative_to(vault)
    except ValueError as exc:
        raise ValueError("WebView2 runtime remediation evidence root must stay inside the vault workspace") from exc
    return root


def _resolve_inside_vault(vault: Path, path: str | Path, *, label: str) -> Path:
    selected = Path(path)
    if not selected.is_absolute():
        selected = vault / selected
    selected = selected.resolve()
    try:
        selected.relative_to(vault)
    except ValueError as exc:
        raise ValueError(f"{label} must stay inside the vault workspace") from exc
    return selected


def _clean(value: str | None) -> str:
    return (value or "").strip()


def _string_value(payload: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def load_webview2_runtime_remediation_evidence_file(
    vault_root: str | Path,
    evidence_file_path: str | Path,
) -> dict[str, str | None]:
    """Load operator-supplied remediation evidence from a vault-scoped JSON file."""

    vault = _vault_path(vault_root)
    selected = _resolve_inside_vault(vault, evidence_file_path, label="WebView2 remediation evidence file")
    try:
        payload = json.loads(selected.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"WebView2 remediation evidence file could not be read: {exc}") from exc
    if payload.get("action") and isinstance(payload.get("result"), dict):
        payload = payload["result"]
    remediation = payload.get("remediation") if isinstance(payload.get("remediation"), dict) else {}
    merged = {**payload, **remediation}
    return {
        "remediation_status": _string_value(merged, "remediation_status", "status"),
        "operator": _string_value(merged, "operator", "remediator", "operator_role"),
        "remediation_summary": _string_value(merged, "remediation_summary", "summary"),
        "evidence_reference": _string_value(merged, "evidence_reference", "reference"),
        "webview2_version": _string_value(merged, "webview2_version", "version"),
        "remediation_timestamp": _string_value(merged, "remediation_timestamp", "timestamp"),
    }


def build_webview2_runtime_remediation_evidence(
    vault_root: str | Path,
    *,
    remediation_status: str = "unknown",
    operator: str | None = None,
    remediation_summary: str | None = None,
    evidence_reference: str | None = None,
    webview2_version: str | None = None,
    remediation_timestamp: str | None = None,
) -> dict[str, Any]:
    """Record supplied remediation evidence without performing or verifying host repair."""

    vault = _vault_path(vault_root)
    status_value = _clean(remediation_status).lower()
    if status_value not in ALLOWED_REMEDIATION_STATUSES:
        raise ValueError(
            "remediation_status must be one of: "
            + ", ".join(sorted(ALLOWED_REMEDIATION_STATUSES))
        )

    operator_value = _clean(operator)
    summary_value = _clean(remediation_summary)
    reference_value = _clean(evidence_reference)
    version_value = _clean(webview2_version)
    timestamp_value = _clean(remediation_timestamp)

    blockers: list[str] = []
    if not operator_value:
        blockers.append("Operator/remediator identity or role was not supplied.")
    if not summary_value:
        blockers.append("Remediation summary was not supplied.")
    if status_value != "performed":
        blockers.append("Operator/admin WebView2 runtime remediation has not been recorded as performed.")
    if status_value == "performed" and not reference_value:
        blockers.append("Performed remediation requires an evidence reference.")

    evidence_supplied = status_value == "performed" and not blockers
    status = (
        "webview2_runtime_remediation_evidence_supplied"
        if evidence_supplied
        else "webview2_runtime_remediation_evidence_not_supplied"
    )
    next_pass = (
        "pass10b-pywebview-webview2-minimal-repro-rerun-after-operator-remediation"
        if evidence_supplied
        else "operator-remediate-webview2-runtime-then-pass10b-minimal-repro-rerun"
    )

    return {
        "ok": evidence_supplied,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "status": status,
        "generated_at": _now_utc(),
        "vault_root": str(vault),
        "remediation": {
            "status": status_value,
            "operator": operator_value,
            "summary": summary_value,
            "evidence_reference": reference_value,
            "webview2_version": version_value,
            "remediation_timestamp": timestamp_value,
        },
        "readiness": {
            "operator_remediation_evidence_supplied": evidence_supplied,
            "remediation_effect_verified": False,
            "requires_minimal_repro_rerun": True,
            "requires_packaged_visual_qa_rerun": evidence_supplied,
            "can_close_pass10b_native_visual_proof": False,
            "next_recommended_pass": next_pass,
            "blockers": blockers,
        },
        "authority": {
            "review_only": True,
            "mutates_host_policy": False,
            "installs_webview2": False,
            "repairs_webview2": False,
            "signs_executable": False,
            "allowlists_executable": False,
            "writes_installer": False,
            "writes_host_startup": False,
            "launches_packaged_executable": False,
            "captures_native_screenshot": False,
            "grants_approvals": False,
            "executes_approval_decisions": False,
            "provider_calls_allowed": False,
            "connector_calls_allowed": False,
            "writes_agent_bus_tasks": False,
            "canonical_mutation_allowed": False,
        },
        "checks": [
            {"name": "remediation_status_allowed", "ok": True, "detail": status_value},
            {"name": "operator_supplied", "ok": bool(operator_value), "detail": operator_value or "missing"},
            {"name": "summary_supplied", "ok": bool(summary_value), "detail": "present" if summary_value else "missing"},
            {"name": "performed_evidence_reference_supplied", "ok": bool(reference_value) if status_value == "performed" else False, "detail": reference_value or "missing"},
            {
                "name": "remediation_effect_verified",
                "ok": False,
                "detail": "evidence intake records operator evidence only; rerun minimal repro and packaged visual QA to verify effect",
            },
            {
                "name": "review_only_boundary",
                "ok": True,
                "detail": "does not install, repair, mutate host policy, launch packaged apps, capture screenshots, or mutate canonical state",
            },
        ],
        "blockers": blockers,
        "unverified": [
            "This intake does not prove the WebView2 runtime now works.",
            "Minimal PyWebView/WebView2 repro must be rerun after operator remediation.",
            "Packaged Studio native visual QA remains unverified until it captures a nonblank native screenshot.",
        ],
        "next_recommended_pass": next_pass,
    }


def format_webview2_runtime_remediation_evidence(report: dict[str, Any]) -> str:
    remediation = report.get("remediation") or {}
    readiness = report.get("readiness") or {}
    lines = [
        f"WebView2 runtime remediation evidence: {report.get('status')}",
        f"  ok: {report.get('ok')}",
        f"  remediation_status: {remediation.get('status')}",
        f"  operator: {remediation.get('operator')}",
        f"  evidence_reference: {remediation.get('evidence_reference')}",
        f"  remediation_effect_verified: {readiness.get('remediation_effect_verified')}",
        f"  next: {report.get('next_recommended_pass')}",
    ]
    for blocker in report.get("blockers") or []:
        lines.append(f"  blocker: {blocker}")
    return "\n".join(lines)


def write_webview2_runtime_remediation_evidence(
    vault_root: str | Path,
    report: dict[str, Any],
    *,
    report_slug: str | None = None,
    report_root: str | Path | None = None,
) -> dict[str, Any]:
    """Write review-only remediation evidence inside the vault workspace."""

    vault = _vault_path(vault_root)
    root = _resolve_report_root(vault, report_root)
    slug = report_slug or f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}-webview2-runtime-remediation-evidence"
    if slug.endswith(".json"):
        slug = slug[:-5]
    json_path = (root / f"{slug}.json").resolve()
    markdown_path = (root / f"{slug}.md").resolve()
    for path in (json_path, markdown_path):
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise ValueError("WebView2 runtime remediation evidence output must stay inside the report root") from exc
    root.mkdir(parents=True, exist_ok=True)

    payload = {
        "report_type": "webview2_runtime_remediation_evidence_intake",
        "generated_at": _now_utc(),
        "status": report.get("status"),
        "ok": bool(report.get("ok")),
        "surface": report.get("surface"),
        "model_version": report.get("model_version"),
        "remediation": report.get("remediation"),
        "readiness": report.get("readiness"),
        "authority": report.get("authority"),
        "evidence_file": report.get("evidence_file"),
        "checks": report.get("checks"),
        "blockers": report.get("blockers"),
        "unverified": report.get("unverified"),
        "next_recommended_pass": report.get("next_recommended_pass"),
        "authority_note": (
            "This evidence intake is review-only. It records operator/admin remediation evidence but does not "
            "install or repair WebView2, mutate host policy, sign or allowlist files, write installer/startup "
            "state, execute approvals, call providers/connectors, write Agent Bus tasks, launch packaged apps, "
            "capture screenshots, or mutate canonical state."
        ),
    }
    json_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

    remediation = report.get("remediation") or {}
    readiness = report.get("readiness") or {}
    checks = report.get("checks") or []
    lines = [
        "# WebView2 Runtime Remediation Evidence Intake",
        "",
        f"Generated: {payload['generated_at']}",
        "Runtime: Codex",
        f"Status: {payload['status']}",
        f"OK: {payload['ok']}",
        f"Remediation status: {remediation.get('status')}",
        f"Operator: {remediation.get('operator')}",
        f"Evidence reference: {remediation.get('evidence_reference')}",
        f"WebView2 version: {remediation.get('webview2_version')}",
        f"Remediation timestamp: {remediation.get('remediation_timestamp')}",
        f"Next recommended pass: {payload['next_recommended_pass']}",
        "",
        "## Summary",
        "",
        remediation.get("summary") or "No remediation summary supplied.",
        "",
        "## Readiness",
        "",
        f"- operator_remediation_evidence_supplied: {readiness.get('operator_remediation_evidence_supplied')}",
        f"- remediation_effect_verified: {readiness.get('remediation_effect_verified')}",
        f"- requires_minimal_repro_rerun: {readiness.get('requires_minimal_repro_rerun')}",
        f"- requires_packaged_visual_qa_rerun: {readiness.get('requires_packaged_visual_qa_rerun')}",
        f"- can_close_pass10b_native_visual_proof: {readiness.get('can_close_pass10b_native_visual_proof')}",
        "",
        "## Checks",
        "",
    ]
    for item in checks:
        lines.append(f"- {item.get('name')}: {item.get('ok')} - {item.get('detail')}")
    blockers = report.get("blockers") or []
    if blockers:
        lines.extend(["", "## Blockers", ""])
        lines.extend(f"- {blocker}" for blocker in blockers)
    lines.extend(
        [
            "",
            "## Authority Boundary",
            "",
            "- This report is review-only operator remediation evidence intake.",
            "- It does not verify the remediation effect; minimal repro and packaged visual QA must be rerun.",
            "- It does not install or repair WebView2, mutate host policy, sign or allowlist files, write installer/startup state, execute approvals, call providers/connectors, write Agent Bus tasks, launch packaged apps, capture screenshots, or mutate canonical state.",
            "",
        ]
    )
    markdown_path.write_text("\n".join(lines), encoding="utf-8")
    return {
        "written": True,
        "json_path": _relative_to_vault(vault, json_path),
        "markdown_path": _relative_to_vault(vault, markdown_path),
    }
