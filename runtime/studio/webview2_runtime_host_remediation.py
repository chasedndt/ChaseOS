"""Review-only WebView2 runtime host remediation handoff for Pass 10B."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from runtime.studio.packaged_app_launch_smoke import _relative_to_vault
from runtime.studio.packaged_app_webview2_diagnostic import DEFAULT_REPORT_ROOT as WEBVIEW2_DIAGNOSTIC_ROOT
from runtime.studio.packaged_app_webview2_policy_check import DEFAULT_REPORT_ROOT as WEBVIEW2_POLICY_ROOT
from runtime.studio.pywebview_webview2_minimal_repro import (
    DEFAULT_REPORT_ROOT as PYWEBVIEW_MINIMAL_REPRO_ROOT,
)


MODEL_VERSION = "studio.webview2_runtime_host_remediation.v1"
SURFACE_ID = "studio_webview2_runtime_host_remediation"
DEFAULT_REPORT_ROOT = Path("07_LOGS") / "Studio-Graph-Views" / "webview2-runtime-host-remediation"


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
        raise ValueError("WebView2 runtime host remediation report root must stay inside the vault workspace") from exc
    return root


def _load_report(vault: Path, report_path: str | Path | None, default_root: Path, expected_surface: str) -> dict[str, Any]:
    selected = Path(report_path) if report_path else _latest_json(vault / default_root)
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
    return {
        "ok": payload.get("surface") == expected_surface,
        "path": _relative_to_vault(vault, selected),
        "artifact_present": True,
        "payload": payload,
        "reason": "Report loaded.",
    }


def _authority_boundary(payload: dict[str, Any]) -> bool:
    authority = payload.get("authority") or {}
    return not any(
        bool(authority.get(key))
        for key in (
            "mutates_host_policy",
            "installs_webview2",
            "signs_executable",
            "allowlists_executable",
            "writes_installer",
            "writes_host_startup",
            "grants_approvals",
            "executes_approval_decisions",
            "provider_calls_allowed",
            "connector_calls_allowed",
            "writes_agent_bus_tasks",
            "canonical_mutation_allowed",
        )
    )


def _minimal_runtime_statuses(payload: dict[str, Any]) -> dict[str, Any]:
    source_probe = payload.get("source_probe") or {}
    visual_probe = payload.get("visual_probe") or {}
    source_runtime = (source_probe.get("launch") or {}).get("runtime_error") or {}
    packaged_runtime = (visual_probe.get("launch") or {}).get("runtime_error") or {}
    return {
        "source_probe_status": source_probe.get("status"),
        "packaged_visual_probe_status": visual_probe.get("status"),
        "source_runtime_error_status": source_runtime.get("status"),
        "packaged_runtime_error_status": packaged_runtime.get("status"),
        "source_runtime_blocked": bool(source_runtime.get("blocked")),
        "packaged_runtime_blocked": bool(packaged_runtime.get("blocked")),
    }


def build_webview2_runtime_host_remediation(
    vault_root: str | Path,
    *,
    minimal_repro_report_path: str | Path | None = None,
    diagnostic_report_path: str | Path | None = None,
    policy_check_report_path: str | Path | None = None,
) -> dict[str, Any]:
    """Build a review-only operator handoff without installing or repairing WebView2."""

    vault = _vault_path(vault_root)
    minimal_loaded = _load_report(
        vault,
        minimal_repro_report_path,
        PYWEBVIEW_MINIMAL_REPRO_ROOT,
        "studio_pywebview_webview2_minimal_repro",
    )
    diagnostic_loaded = _load_report(
        vault,
        diagnostic_report_path,
        WEBVIEW2_DIAGNOSTIC_ROOT,
        "studio_packaged_app_webview2_diagnostic",
    )
    policy_loaded = _load_report(
        vault,
        policy_check_report_path,
        WEBVIEW2_POLICY_ROOT,
        "studio_packaged_app_webview2_policy_check",
    )
    minimal_payload = minimal_loaded.get("payload") or {}
    diagnostic_payload = diagnostic_loaded.get("payload") or {}
    policy_payload = policy_loaded.get("payload") or {}
    runtime_statuses = _minimal_runtime_statuses(minimal_payload)
    minimal_authority = _authority_boundary(minimal_payload)
    diagnostic_authority = True if not diagnostic_loaded.get("artifact_present") else _authority_boundary(diagnostic_payload)
    policy_authority = True if not policy_loaded.get("artifact_present") else _authority_boundary(policy_payload)
    minimal_points_to_remediation = minimal_payload.get("next_recommended_pass") == "pass10b-webview2-runtime-host-remediation"
    source_and_packaged_blocked = bool(
        runtime_statuses["source_runtime_blocked"]
        and runtime_statuses["packaged_runtime_blocked"]
        and runtime_statuses["source_runtime_error_status"] == "webview2_initialization_failed"
        and runtime_statuses["packaged_runtime_error_status"] == "webview2_initialization_failed"
    )

    blockers: list[str] = []
    if not minimal_loaded.get("ok"):
        blockers.append("Minimal PyWebView/WebView2 repro report is missing or invalid.")
    if minimal_loaded.get("ok") and not minimal_points_to_remediation:
        blockers.append("Minimal repro does not currently route to WebView2 runtime host remediation.")
    if minimal_loaded.get("ok") and not source_and_packaged_blocked:
        blockers.append("Minimal repro does not prove both source and packaged PyWebView fail WebView2 initialization.")
    if not minimal_authority:
        blockers.append("Minimal repro authority boundary is not acceptable for host-remediation handoff.")
    if not diagnostic_authority:
        blockers.append("WebView2 diagnostic authority boundary is not acceptable for host-remediation handoff.")
    if not policy_authority:
        blockers.append("WebView2 policy-check authority boundary is not acceptable for host-remediation handoff.")

    ok = not blockers
    status = "webview2_runtime_host_remediation_ready" if ok else "webview2_runtime_host_remediation_blocked"
    minimal_command = (
        "python -m chaseos studio pywebview-webview2-minimal-repro "
        "--probe-source --probe-launch --write-report --json"
    )
    packaged_visual_qa_command = (
        "python -m chaseos studio packaged-app-visual-qa "
        "--settle-seconds 12 --window-timeout-seconds 30 --terminate-timeout-seconds 5 --json"
    )
    completion_audit_command = (
        "python -m chaseos studio pass10b-visual-proof-completion-audit "
        "--probe-native-host-policy --native-probe-settle-seconds 2 "
        "--native-probe-window-timeout-seconds 5 --native-probe-terminate-timeout-seconds 3 "
        "--write-report --json"
    )

    return {
        "ok": ok,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "status": status,
        "generated_at": _now_utc(),
        "vault_root": str(vault),
        "latest_minimal_repro": {
            "path": minimal_loaded.get("path"),
            "artifact_present": minimal_loaded.get("artifact_present"),
            "report_status": minimal_payload.get("status"),
            "report_ok": bool(minimal_payload.get("ok")),
            "next_recommended_pass": minimal_payload.get("next_recommended_pass"),
            **runtime_statuses,
        },
        "latest_webview2_diagnostic": {
            "path": diagnostic_loaded.get("path"),
            "artifact_present": diagnostic_loaded.get("artifact_present"),
            "report_status": diagnostic_payload.get("status"),
            "report_ok": bool(diagnostic_payload.get("ok")),
            "next_recommended_pass": diagnostic_payload.get("next_recommended_pass"),
            "runtime_status": ((diagnostic_payload.get("webview2_runtime") or {}).get("status")),
            "runtime_detected": ((diagnostic_payload.get("webview2_runtime") or {}).get("runtime_detected")),
        },
        "latest_webview2_policy_check": {
            "path": policy_loaded.get("path"),
            "artifact_present": policy_loaded.get("artifact_present"),
            "report_status": policy_payload.get("status"),
            "report_ok": bool(policy_payload.get("ok")),
            "next_recommended_pass": policy_payload.get("next_recommended_pass"),
            "policy_detected": ((policy_payload.get("webview2_policy") or {}).get("policy_detected")),
        },
        "operator_handoff": {
            "required_external_actions": [
                "Operator/admin repairs or reinstalls the Microsoft Edge WebView2 Runtime if host repair is available and appropriate.",
                "Operator/admin reviews enterprise or endpoint controls that can block WebView2 controller creation for PyWebView/WinForms hosts.",
                "Operator/admin confirms the current user can launch WebView2 outside ChaseOS after repair.",
                "Rerun the minimal PyWebView/WebView2 source and packaged repro after remediation.",
                "Rerun packaged Studio native visual QA only after the minimal repro opens a visible nonblank window.",
            ],
            "acceptance_criteria": [
                "`source_runtime_error_status` is absent or not `webview2_initialization_failed`",
                "`packaged_runtime_error_status` is absent or not `webview2_initialization_failed`",
                "`window_capture_ok=true` for the minimal packaged repro",
                "`screenshot_nonblank=true` for the minimal packaged repro",
                "`window_capture_ok=true` and `screenshot_nonblank=true` for packaged Studio before Pass 10B can close",
            ],
            "minimal_repro_command": minimal_command,
            "packaged_visual_qa_command": packaged_visual_qa_command,
            "completion_audit_command": completion_audit_command,
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
            {"name": "minimal_repro_report_loaded", "ok": bool(minimal_loaded.get("ok")), "detail": minimal_loaded.get("path")},
            {"name": "minimal_repro_routes_to_host_remediation", "ok": minimal_points_to_remediation, "detail": minimal_payload.get("next_recommended_pass")},
            {"name": "source_pywebview_webview2_blocked", "ok": bool(runtime_statuses["source_runtime_blocked"]), "detail": runtime_statuses["source_runtime_error_status"]},
            {"name": "packaged_pywebview_webview2_blocked", "ok": bool(runtime_statuses["packaged_runtime_blocked"]), "detail": runtime_statuses["packaged_runtime_error_status"]},
            {"name": "minimal_repro_authority_boundary", "ok": minimal_authority, "detail": minimal_payload.get("authority")},
            {"name": "diagnostic_authority_boundary", "ok": diagnostic_authority, "detail": diagnostic_payload.get("authority")},
            {"name": "policy_authority_boundary", "ok": policy_authority, "detail": policy_payload.get("authority")},
            {"name": "review_only_boundary", "ok": True, "detail": "report does not install, repair, or mutate WebView2 or host policy"},
        ],
        "blockers": blockers,
        "unverified": [
            "WebView2 runtime repair/reinstall must be performed outside Codex by the operator or host administrator.",
            "Enterprise or endpoint controls affecting WebView2 controller creation were not changed.",
            "Native packaged Studio visual QA remains unverified until the minimal repro and Studio executable capture nonblank screenshots.",
        ],
        "next_recommended_pass": "operator-remediate-webview2-runtime-then-pass10b-minimal-repro-rerun",
    }


def format_webview2_runtime_host_remediation(report: dict[str, Any]) -> str:
    latest = report.get("latest_minimal_repro") or {}
    lines = [
        f"WebView2 Runtime Host Remediation: {report.get('status')}",
        f"  ok: {report.get('ok')}",
        f"  minimal_repro: {latest.get('path')}",
        f"  source_runtime: {latest.get('source_runtime_error_status')}",
        f"  packaged_runtime: {latest.get('packaged_runtime_error_status')}",
        f"  next: {report.get('next_recommended_pass')}",
    ]
    for blocker in report.get("blockers") or []:
        lines.append(f"  blocker: {blocker}")
    return "\n".join(lines)


def write_webview2_runtime_host_remediation(
    vault_root: str | Path,
    report: dict[str, Any],
    *,
    report_slug: str | None = None,
    report_root: str | Path | None = None,
) -> dict[str, Any]:
    vault = _vault_path(vault_root)
    root = _resolve_report_root(vault, report_root)
    slug = report_slug or f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}-webview2-runtime-host-remediation"
    json_path = (root / f"{slug}.json").resolve()
    markdown_path = (root / f"{slug}.md").resolve()
    for path in (json_path, markdown_path):
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise ValueError("WebView2 runtime host remediation output must stay inside the report root") from exc
    root.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    handoff = report.get("operator_handoff") or {}
    lines = [
        "# WebView2 Runtime Host Remediation Handoff",
        "",
        f"Generated: {report.get('generated_at')}",
        "Runtime: Codex",
        f"Status: {report.get('status')}",
        f"OK: {report.get('ok')}",
        f"Next recommended pass: {report.get('next_recommended_pass')}",
        "",
        "## Evidence",
        "",
        f"- Minimal repro: {(report.get('latest_minimal_repro') or {}).get('path')}",
        f"- Source runtime: {(report.get('latest_minimal_repro') or {}).get('source_runtime_error_status')}",
        f"- Packaged runtime: {(report.get('latest_minimal_repro') or {}).get('packaged_runtime_error_status')}",
        f"- WebView2 diagnostic: {(report.get('latest_webview2_diagnostic') or {}).get('path')}",
        f"- WebView2 policy check: {(report.get('latest_webview2_policy_check') or {}).get('path')}",
        "",
        "## Required External Actions",
        "",
        *[f"- {item}" for item in handoff.get("required_external_actions") or []],
        "",
        "## Acceptance Criteria",
        "",
        *[f"- {item}" for item in handoff.get("acceptance_criteria") or []],
        "",
        "## Rerun Commands",
        "",
        f"- Minimal repro: `{handoff.get('minimal_repro_command')}`",
        f"- Packaged visual QA: `{handoff.get('packaged_visual_qa_command')}`",
        f"- Completion audit: `{handoff.get('completion_audit_command')}`",
        "",
        "## Authority",
        "",
        *[f"- {key}: {value}" for key, value in (report.get("authority") or {}).items()],
    ]
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "written": True,
        "json_path": _relative_to_vault(vault, json_path),
        "markdown_path": _relative_to_vault(vault, markdown_path),
    }
