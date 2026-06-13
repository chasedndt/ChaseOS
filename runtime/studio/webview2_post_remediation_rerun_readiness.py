"""Read-only readiness gate for Pass 10B WebView2 post-remediation reruns."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from runtime.studio.packaged_app_launch_smoke import _relative_to_vault
from runtime.studio.webview2_runtime_host_remediation import (
    DEFAULT_REPORT_ROOT as HOST_REMEDIATION_ROOT,
)
from runtime.studio.webview2_runtime_remediation_evidence import (
    DEFAULT_REPORT_ROOT as REMEDIATION_EVIDENCE_ROOT,
)


MODEL_VERSION = "studio.webview2_post_remediation_rerun_readiness.v1"
SURFACE_ID = "studio_webview2_post_remediation_rerun_readiness"
DEFAULT_REPORT_ROOT = Path("07_LOGS") / "Studio-Graph-Views" / "webview2-post-remediation-rerun-readiness"


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _latest_json(root: Path) -> Path | None:
    if not root.is_dir():
        return None
    candidates = [path for path in root.glob("*.json") if path.is_file()]
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


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


def _resolve_report_root(vault: Path, report_root: str | Path | None) -> Path:
    root = Path(report_root) if report_root else DEFAULT_REPORT_ROOT
    if not root.is_absolute():
        root = vault / root
    root = root.resolve()
    try:
        root.relative_to(vault)
    except ValueError as exc:
        raise ValueError("WebView2 post-remediation rerun readiness root must stay inside the vault workspace") from exc
    return root


def _load_report(vault: Path, path: str | Path | None, default_root: Path, expected_surface: str) -> dict[str, Any]:
    selected = Path(path) if path else _latest_json(vault / default_root)
    if selected is None:
        return {
            "ok": False,
            "path": None,
            "artifact_present": False,
            "payload": None,
            "reason": "No report was found.",
        }
    selected = _resolve_inside_vault(vault, selected, label=f"{expected_surface} report")
    try:
        payload = json.loads(selected.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "ok": False,
            "path": _relative_to_vault(vault, selected),
            "artifact_present": True,
            "payload": None,
            "reason": f"Report could not be read: {exc}",
        }
    if payload.get("action") and isinstance(payload.get("result"), dict):
        payload = payload["result"]
    surface_valid = payload.get("surface") == expected_surface
    return {
        "ok": surface_valid,
        "path": _relative_to_vault(vault, selected),
        "artifact_present": True,
        "payload": payload,
        "reason": "Report loaded." if surface_valid else "Report surface did not match.",
    }


def _review_only_authority(payload: dict[str, Any]) -> bool:
    authority = payload.get("authority") or {}
    return bool(authority.get("review_only")) and not any(
        bool(authority.get(key))
        for key in (
            "mutates_host_policy",
            "installs_webview2",
            "repairs_webview2",
            "signs_executable",
            "allowlists_executable",
            "writes_installer",
            "writes_host_startup",
            "launches_packaged_executable",
            "captures_native_screenshot",
            "grants_approvals",
            "executes_approval_decisions",
            "provider_calls_allowed",
            "connector_calls_allowed",
            "writes_agent_bus_tasks",
            "canonical_mutation_allowed",
        )
    )


def build_webview2_post_remediation_rerun_readiness(
    vault_root: str | Path,
    *,
    remediation_evidence_path: str | Path | None = None,
    host_remediation_report_path: str | Path | None = None,
) -> dict[str, Any]:
    """Build a fail-closed rerun plan without executing the rerun."""

    vault = _vault_path(vault_root)
    host_loaded = _load_report(
        vault,
        host_remediation_report_path,
        HOST_REMEDIATION_ROOT,
        "studio_webview2_runtime_host_remediation",
    )
    evidence_loaded = _load_report(
        vault,
        remediation_evidence_path,
        REMEDIATION_EVIDENCE_ROOT,
        "studio_webview2_runtime_remediation_evidence",
    )
    host_payload = host_loaded.get("payload") or {}
    evidence_payload = evidence_loaded.get("payload") or {}
    readiness = evidence_payload.get("readiness") or {}
    remediation = evidence_payload.get("remediation") or {}
    host_authority = _review_only_authority(host_payload) if host_loaded.get("artifact_present") else False
    evidence_authority = _review_only_authority(evidence_payload) if evidence_loaded.get("artifact_present") else False
    evidence_supplied = bool(readiness.get("operator_remediation_evidence_supplied"))
    remediation_effect_verified = bool(readiness.get("remediation_effect_verified"))

    blockers: list[str] = []
    if not host_loaded.get("ok"):
        blockers.append("WebView2 runtime host-remediation handoff/report is missing or invalid.")
    if host_loaded.get("artifact_present") and not host_authority:
        blockers.append("WebView2 host-remediation handoff authority boundary is not acceptable.")
    if not evidence_loaded.get("ok"):
        blockers.append("WebView2 runtime remediation evidence report is missing or invalid.")
    if evidence_loaded.get("artifact_present") and not evidence_authority:
        blockers.append("WebView2 runtime remediation evidence authority boundary is not acceptable.")
    if not evidence_supplied:
        blockers.append("Operator/admin WebView2 remediation evidence has not been supplied.")
    if remediation_effect_verified:
        blockers.append("Remediation evidence intake must not claim rerun verification before reruns execute.")

    ok = not blockers
    status = "webview2_post_remediation_rerun_ready" if ok else "blocked_webview2_post_remediation_rerun_readiness"
    minimal_repro_command = (
        "python -m runtime.cli.main studio pywebview-webview2-minimal-repro "
        "--probe-source --probe-launch --write-report --json"
    )
    packaged_visual_qa_command = (
        "python -m runtime.cli.main studio packaged-app-visual-qa "
        "--settle-seconds 12 --window-timeout-seconds 30 --terminate-timeout-seconds 5 --json"
    )
    completion_audit_command = (
        "python -m runtime.cli.main studio pass10b-visual-proof-completion-audit "
        "--probe-native-host-policy --native-probe-settle-seconds 2 "
        "--native-probe-window-timeout-seconds 5 --native-probe-terminate-timeout-seconds 3 "
        f"--webview2-remediation-evidence-path {evidence_loaded.get('path') or '<remediation-evidence.json>'} "
        "--write-report --json"
    )
    next_pass = (
        "pass10b-pywebview-webview2-minimal-repro-rerun-after-operator-remediation"
        if ok
        else "operator-remediate-webview2-runtime-then-pass10b-minimal-repro-rerun"
    )

    return {
        "ok": ok,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "status": status,
        "generated_at": _now_utc(),
        "vault_root": str(vault),
        "host_remediation_handoff": {
            "path": host_loaded.get("path"),
            "artifact_present": host_loaded.get("artifact_present"),
            "report_status": host_payload.get("status"),
            "report_ok": bool(host_payload.get("ok")),
            "authority_boundary_present": host_authority,
            "next_recommended_pass": host_payload.get("next_recommended_pass"),
        },
        "remediation_evidence": {
            "path": evidence_loaded.get("path"),
            "artifact_present": evidence_loaded.get("artifact_present"),
            "report_status": evidence_payload.get("status"),
            "report_ok": bool(evidence_payload.get("ok")),
            "remediation_status": remediation.get("status"),
            "operator": remediation.get("operator"),
            "evidence_reference": remediation.get("evidence_reference"),
            "operator_remediation_evidence_supplied": evidence_supplied,
            "remediation_effect_verified": remediation_effect_verified,
            "authority_boundary_present": evidence_authority,
            "next_recommended_pass": evidence_payload.get("next_recommended_pass"),
        },
        "rerun_plan": {
            "ready": ok,
            "minimal_repro_command": minimal_repro_command,
            "packaged_visual_qa_command": packaged_visual_qa_command,
            "completion_audit_command": completion_audit_command,
            "rerun_order": [
                "Rerun minimal source and packaged PyWebView/WebView2 repro.",
                "Only if minimal repro no longer fails WebView2 initialization, rerun packaged Studio visual QA.",
                "Rerun Pass 10B completion audit with remediation evidence and fresh packaged visual-QA evidence.",
            ],
        },
        "authority": {
            "review_only": True,
            "executes_reruns": False,
            "launches_packaged_executable": False,
            "captures_native_screenshot": False,
            "mutates_host_policy": False,
            "installs_webview2": False,
            "repairs_webview2": False,
            "signs_executable": False,
            "allowlists_executable": False,
            "writes_installer": False,
            "writes_host_startup": False,
            "grants_approvals": False,
            "executes_approval_decisions": False,
            "provider_calls_allowed": False,
            "connector_calls_allowed": False,
            "writes_agent_bus_tasks": False,
            "canonical_mutation_allowed": False,
        },
        "checks": [
            {"name": "host_remediation_handoff_loaded", "ok": bool(host_loaded.get("ok")), "detail": host_loaded.get("path")},
            {"name": "host_remediation_handoff_review_only", "ok": host_authority, "detail": host_payload.get("authority")},
            {"name": "remediation_evidence_loaded", "ok": bool(evidence_loaded.get("ok")), "detail": evidence_loaded.get("path")},
            {"name": "remediation_evidence_review_only", "ok": evidence_authority, "detail": evidence_payload.get("authority")},
            {"name": "operator_remediation_evidence_supplied", "ok": evidence_supplied, "detail": remediation.get("status")},
            {"name": "remediation_effect_not_preclaimed", "ok": not remediation_effect_verified, "detail": remediation_effect_verified},
            {"name": "rerun_plan_ready", "ok": ok, "detail": next_pass},
        ],
        "blockers": blockers,
        "unverified": [
            "This readiness gate does not execute the minimal repro.",
            "This readiness gate does not execute packaged Studio visual QA.",
            "This readiness gate does not verify WebView2 remediation effects.",
        ],
        "next_recommended_pass": next_pass,
    }


def format_webview2_post_remediation_rerun_readiness(report: dict[str, Any]) -> str:
    evidence = report.get("remediation_evidence") or {}
    lines = [
        f"WebView2 post-remediation rerun readiness: {report.get('status')}",
        f"  ok: {report.get('ok')}",
        f"  evidence: {evidence.get('path')}",
        f"  remediation_status: {evidence.get('remediation_status')}",
        f"  operator_evidence_supplied: {evidence.get('operator_remediation_evidence_supplied')}",
        f"  next: {report.get('next_recommended_pass')}",
    ]
    for blocker in report.get("blockers") or []:
        lines.append(f"  blocker: {blocker}")
    return "\n".join(lines)


def write_webview2_post_remediation_rerun_readiness(
    vault_root: str | Path,
    report: dict[str, Any],
    *,
    report_slug: str | None = None,
    report_root: str | Path | None = None,
) -> dict[str, Any]:
    """Write a rerun-readiness report inside the vault workspace."""

    vault = _vault_path(vault_root)
    root = _resolve_report_root(vault, report_root)
    slug = report_slug or f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}-webview2-post-remediation-rerun-readiness"
    if slug.endswith(".json"):
        slug = slug[:-5]
    json_path = (root / f"{slug}.json").resolve()
    markdown_path = (root / f"{slug}.md").resolve()
    for path in (json_path, markdown_path):
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise ValueError("WebView2 post-remediation rerun readiness output must stay inside the report root") from exc
    root.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")

    rerun = report.get("rerun_plan") or {}
    lines = [
        "# WebView2 Post-Remediation Rerun Readiness",
        "",
        f"Generated: {report.get('generated_at')}",
        "Runtime: Codex",
        f"Status: {report.get('status')}",
        f"OK: {report.get('ok')}",
        f"Next recommended pass: {report.get('next_recommended_pass')}",
        "",
        "## Rerun Plan",
        "",
        f"- Ready: {rerun.get('ready')}",
        f"- Minimal repro: `{rerun.get('minimal_repro_command')}`",
        f"- Packaged visual QA: `{rerun.get('packaged_visual_qa_command')}`",
        f"- Completion audit: `{rerun.get('completion_audit_command')}`",
        "",
        "## Blockers",
        "",
    ]
    blockers = report.get("blockers") or []
    lines.extend(f"- {blocker}" for blocker in blockers) if blockers else lines.append("- None")
    lines.extend(
        [
            "",
            "## Authority Boundary",
            "",
            "- This report is review-only and does not execute reruns.",
            "- It does not install or repair WebView2, mutate host policy, launch packaged apps, capture screenshots, sign or allowlist files, write installer/startup state, execute approvals, call providers/connectors, write Agent Bus tasks, or mutate canonical state.",
            "",
        ]
    )
    markdown_path.write_text("\n".join(lines), encoding="utf-8")
    return {
        "written": True,
        "json_path": _relative_to_vault(vault, json_path),
        "markdown_path": _relative_to_vault(vault, markdown_path),
    }
