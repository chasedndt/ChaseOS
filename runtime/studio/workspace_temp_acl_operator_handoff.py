"""Review-only workspace temp ACL operator handoff for Pass 10B."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from runtime.studio.packaged_app_launch_smoke import _relative_to_vault
from runtime.studio.workspace_temp_acl_cleanup_diagnostic import (
    DEFAULT_REPORT_ROOT as WORKSPACE_TEMP_DIAGNOSTIC_ROOT,
)


MODEL_VERSION = "studio.workspace_temp_acl_operator_handoff.v1"
SURFACE_ID = "studio_workspace_temp_acl_operator_handoff"
DEFAULT_HANDOFF_ROOT = Path("07_LOGS") / "Studio-Graph-Views" / "workspace-temp-acl-operator-handoffs"


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


def _resolve_handoff_root(vault: Path, handoff_root: str | Path | None) -> Path:
    root_input = Path(handoff_root) if handoff_root else DEFAULT_HANDOFF_ROOT
    root = root_input if root_input.is_absolute() else vault / root_input
    root = root.resolve()
    try:
        root.relative_to(vault)
    except ValueError as exc:
        raise ValueError("Workspace temp ACL handoff root must stay inside the vault workspace") from exc
    return root


def _load_diagnostic(vault: Path, diagnostic_report_path: str | Path | None = None) -> dict[str, Any]:
    selected = Path(diagnostic_report_path) if diagnostic_report_path else _latest_json(vault / WORKSPACE_TEMP_DIAGNOSTIC_ROOT)
    if selected is None:
        return {
            "ok": False,
            "path": None,
            "artifact_present": False,
            "payload": None,
            "reason": "No workspace temp ACL cleanup diagnostic report was found.",
        }
    selected = _resolve_inside_vault(vault, selected, label="workspace temp ACL diagnostic report")
    try:
        payload = json.loads(selected.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "ok": False,
            "path": _relative_to_vault(vault, selected),
            "artifact_present": True,
            "payload": None,
            "reason": f"Workspace temp ACL diagnostic report could not be read: {exc}",
        }
    return {
        "ok": payload.get("surface") == "studio_workspace_temp_acl_cleanup_diagnostic",
        "path": _relative_to_vault(vault, selected),
        "artifact_present": True,
        "payload": payload,
        "reason": "Workspace temp ACL cleanup diagnostic report loaded.",
    }


def _blocked_paths(diagnostic: dict[str, Any]) -> list[str]:
    paths: list[str] = []
    owned_probe = diagnostic.get("owned_cleanup_probe") or {}
    if owned_probe.get("created"):
        paths.append(str(owned_probe.get("created")))
    cleanup_error = diagnostic.get("prior_workspace_cleanup_error") or {}
    if cleanup_error.get("path_inside_vault") and cleanup_error.get("path"):
        paths.append(str(cleanup_error.get("path")))
    for item in diagnostic.get("workspace_temp_paths") or []:
        if item.get("error") and item.get("path"):
            paths.append(str(item.get("path")))
    deduped: list[str] = []
    seen: set[str] = set()
    for path in paths:
        if path not in seen:
            seen.add(path)
            deduped.append(path)
    return deduped


def build_workspace_temp_acl_operator_handoff(
    vault_root: str | Path,
    *,
    diagnostic_report_path: str | Path | None = None,
) -> dict[str, Any]:
    """Build a review-only operator handoff without repairing ACLs or deleting artifacts."""

    vault = _vault_path(vault_root)
    loaded = _load_diagnostic(vault, diagnostic_report_path)
    diagnostic = loaded.get("payload") or {}
    diagnostic_status = diagnostic.get("status")
    diagnostic_next = diagnostic.get("next_recommended_pass")
    blocked_paths = _blocked_paths(diagnostic)

    diagnostic_valid = bool(loaded.get("ok"))
    points_to_handoff = diagnostic_next in {
        "pass10b-workspace-temp-acl-operator-handoff",
        "pass10b-workspace-temp-stale-artifact-operator-handoff",
    }
    authority_boundary = not any(
        bool((diagnostic.get("authority") or {}).get(key))
        for key in (
            "deletes_existing_temp_artifacts",
            "mutates_temp_acl",
            "mutates_host_policy",
            "installs_webview2",
            "launches_packaged_executable",
            "captures_native_screenshot",
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

    blockers: list[str] = []
    if not diagnostic_valid:
        blockers.append(str(loaded.get("reason") or "Workspace temp ACL diagnostic report is missing or invalid."))
    if diagnostic_valid and not points_to_handoff:
        blockers.append("Latest workspace temp ACL diagnostic does not currently route to an operator handoff.")
    if not blocked_paths:
        blockers.append("No specific blocked workspace temp paths were extracted for operator review.")
    if not authority_boundary:
        blockers.append("Latest diagnostic authority boundary is not acceptable for a handoff.")

    status = "workspace_temp_acl_operator_handoff_ready" if diagnostic_valid and authority_boundary else "workspace_temp_acl_operator_handoff_blocked"
    ok = bool(status == "workspace_temp_acl_operator_handoff_ready")
    diagnostic_command = (
        "python -m chaseos studio workspace-temp-acl-cleanup-diagnostic "
        "--write-report --json"
    )
    completion_audit_command = (
        "python -m chaseos studio pass10b-visual-proof-completion-audit "
        "--probe-native-host-policy --native-probe-settle-seconds 2 "
        "--native-probe-window-timeout-seconds 5 --native-probe-terminate-timeout-seconds 3 "
        "--write-report --json"
    )
    visual_qa_command = (
        "python -m chaseos studio packaged-app-visual-qa "
        "--settle-seconds 3 --window-timeout-seconds 10 --terminate-timeout-seconds 5 --json"
    )

    return {
        "ok": ok,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "status": status,
        "generated_at": _now_utc(),
        "vault_root": str(vault),
        "latest_workspace_temp_acl_diagnostic": {
            "path": loaded.get("path"),
            "artifact_present": loaded.get("artifact_present"),
            "report_status": diagnostic_status,
            "report_ok": bool(diagnostic.get("ok")),
            "next_recommended_pass": diagnostic_next,
        },
        "blocked_paths": blocked_paths,
        "diagnostic_checks": diagnostic.get("checks") or [],
        "diagnostic_blockers": diagnostic.get("blockers") or [],
        "operator_handoff": {
            "required_external_actions": [
                "Operator/admin inspects the listed workspace temp paths and their parent directories.",
                "Operator/admin repairs workspace temp ACL or ownership so the current user can create, write, list, and remove owned temp children.",
                "Operator/admin removes or repairs stale temp cleanup artifacts only after confirming they are workspace-local diagnostic/runtime leftovers.",
                "Rerun the bounded workspace temp diagnostic before rerunning native packaged visual QA.",
                "Rerun packaged native visual QA only after the diagnostic owned probe can write and clean up successfully.",
            ],
            "acceptance_criteria": [
                "`owned_probe_file_write_ok=true`",
                "`owned_probe_cleanup_ok=true`",
                "`stale_cleanup_error_path_absent=true`",
                "`acl_snapshots_available=true`",
                "`prior_workspace_python_temp_override_ok=true` or a new minimal repro explains the remaining failure",
                "`window_capture_ok=true` and `screenshot_nonblank=true` before Pass 10B can close",
            ],
            "diagnostic_command": diagnostic_command,
            "completion_audit_command": completion_audit_command,
            "visual_qa_command": visual_qa_command,
        },
        "authority": {
            "review_only": True,
            "deletes_existing_temp_artifacts": False,
            "mutates_temp_acl": False,
            "mutates_host_policy": False,
            "installs_webview2": False,
            "launches_packaged_executable": False,
            "captures_native_screenshot": False,
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
            {"name": "workspace_temp_acl_diagnostic_loaded", "ok": diagnostic_valid, "detail": loaded.get("path")},
            {"name": "diagnostic_routes_to_operator_handoff", "ok": points_to_handoff, "detail": diagnostic_next},
            {"name": "blocked_paths_extracted", "ok": bool(blocked_paths), "detail": len(blocked_paths)},
            {"name": "review_only_boundary", "ok": True, "detail": "handoff does not repair ACLs or delete artifacts"},
            {"name": "diagnostic_authority_boundary_present", "ok": authority_boundary, "detail": diagnostic.get("authority")},
        ],
        "blockers": blockers,
        "unverified": [
            "Workspace temp ACL/ownership repair must be performed outside Codex by the operator or host administrator.",
            "Stale temp artifact deletion or repair must be explicitly operator-approved.",
            "Native packaged screenshot proof remains unverified until the bounded visual QA command captures a real nonblank screenshot.",
        ],
        "next_recommended_pass": "operator-repair-workspace-temp-acl-then-pass10b-native-visual-qa-rerun",
    }


def format_workspace_temp_acl_operator_handoff(report: dict[str, Any]) -> str:
    latest = report.get("latest_workspace_temp_acl_diagnostic") or {}
    handoff = report.get("operator_handoff") or {}
    lines = [
        f"Workspace Temp ACL Operator Handoff: {report.get('status')}",
        f"  ok: {report.get('ok')}",
        f"  diagnostic: {latest.get('path')}",
        f"  diagnostic_status: {latest.get('report_status')}",
        f"  blocked_paths: {len(report.get('blocked_paths') or [])}",
        f"  next: {report.get('next_recommended_pass')}",
        f"  diagnostic_command: {handoff.get('diagnostic_command')}",
        f"  visual_qa_command: {handoff.get('visual_qa_command')}",
    ]
    blockers = report.get("blockers") or []
    if blockers:
        lines.append(f"  blockers: {', '.join(str(item) for item in blockers)}")
    return "\n".join(lines)


def write_workspace_temp_acl_operator_handoff(
    vault_root: str | Path,
    report: dict[str, Any],
    *,
    handoff_slug: str | None = None,
    handoff_root: str | Path | None = None,
) -> dict[str, Any]:
    """Write durable operator handoff artifacts without repairing workspace temp state."""

    vault = _vault_path(vault_root)
    root = _resolve_handoff_root(vault, handoff_root)
    slug = handoff_slug or f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}-pass10b-workspace-temp-acl-operator-handoff"
    json_path = (root / f"{slug}.json").resolve()
    markdown_path = (root / f"{slug}.md").resolve()
    for path in (json_path, markdown_path):
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise ValueError("Workspace temp ACL handoff output must stay inside the handoff root") from exc
    root.mkdir(parents=True, exist_ok=True)

    payload = {
        "handoff_type": "pass10b_workspace_temp_acl_operator_handoff",
        "generated_at": _now_utc(),
        "status": report.get("status"),
        "ok": report.get("ok"),
        "latest_workspace_temp_acl_diagnostic": report.get("latest_workspace_temp_acl_diagnostic"),
        "blocked_paths": report.get("blocked_paths"),
        "diagnostic_checks": report.get("diagnostic_checks"),
        "diagnostic_blockers": report.get("diagnostic_blockers"),
        "operator_handoff": report.get("operator_handoff"),
        "authority": report.get("authority"),
        "checks": report.get("checks"),
        "blockers": report.get("blockers"),
        "next_recommended_pass": report.get("next_recommended_pass"),
        "note": "This handoff is review-only. It does not delete temp artifacts, repair ACLs, mutate host policy, install WebView2, launch the packaged app, or complete native visual QA.",
    }
    json_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

    handoff = report.get("operator_handoff") or {}
    actions = handoff.get("required_external_actions") or []
    criteria = handoff.get("acceptance_criteria") or []
    lines = [
        "# Pass 10B Workspace Temp ACL Operator Handoff",
        "",
        f"Generated: {payload['generated_at']}",
        "Runtime: Codex",
        f"Status: {report.get('status')}",
        f"OK: {report.get('ok')}",
        "",
        "## Latest Diagnostic",
        "",
        f"- Path: {(report.get('latest_workspace_temp_acl_diagnostic') or {}).get('path')}",
        f"- Status: {(report.get('latest_workspace_temp_acl_diagnostic') or {}).get('report_status')}",
        f"- Next: {(report.get('latest_workspace_temp_acl_diagnostic') or {}).get('next_recommended_pass')}",
        "",
        "## Blocked Workspace Temp Paths",
        "",
        *[f"- `{item}`" for item in (report.get("blocked_paths") or ["None extracted"])],
        "",
        "## Required External Actions",
        "",
        *[f"- {item}" for item in actions],
        "",
        "## Acceptance Criteria",
        "",
        *[f"- {item}" for item in criteria],
        "",
        "## Rerun Commands",
        "",
        f"- Diagnostic: `{handoff.get('diagnostic_command')}`",
        f"- Completion audit: `{handoff.get('completion_audit_command')}`",
        f"- Visual QA: `{handoff.get('visual_qa_command')}`",
        "",
        "## Authority Boundary",
        "",
        "- This handoff is review-only.",
        "- It does not delete stale temp artifacts.",
        "- It does not mutate temp ACLs, host policy, WebView2 installation, signing, installer, startup, approval, Agent Bus, workflow, provider, connector, graph, or canonical state.",
    ]
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "written": True,
        "json_path": _relative_to_vault(vault, json_path),
        "markdown_path": _relative_to_vault(vault, markdown_path),
    }
