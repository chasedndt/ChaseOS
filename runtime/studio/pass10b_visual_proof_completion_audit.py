"""Read-only Pass 10B visual-proof completion audit."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from runtime.operator_surface.browser.image_verifier import analyze_png_nonblank
from runtime.studio.packaged_app_host_policy_unblock import (
    DEFAULT_HANDOFF_ROOT,
    build_packaged_app_host_policy_unblock_readiness,
)
from runtime.studio.pass10b_native_screenshot_evidence_intake import (
    build_pass10b_native_screenshot_evidence_intake,
)
from runtime.studio.workspace_temp_acl_operator_handoff import (
    DEFAULT_HANDOFF_ROOT as WORKSPACE_TEMP_ACL_HANDOFF_ROOT,
)


MODEL_VERSION = "studio.pass10b_visual_proof_completion_audit.v1"
SURFACE_ID = "studio_pass10b_visual_proof_completion_audit"
BROWSER_NONBLANK_EVIDENCE = (
    Path("07_LOGS")
    / "Operator-Screenshots"
    / "2026-05-10-pass10b-screenshot-nonblank-verifier-graph-route-clip-verified.png"
)
PASS10B_TEST_PATH = Path("runtime") / "studio" / "shell" / "test_pass10b_graph_settings.py"
DESKTOP_SHELL_TEST_PATH = Path("runtime") / "studio" / "test_desktop_shell_app.py"
DEFAULT_REPORT_ROOT = Path("07_LOGS") / "Studio-Graph-Views" / "pass10b-completion-audits"
WEBVIEW2_DIAGNOSTIC_REPORT_ROOT = Path("07_LOGS") / "Studio-Graph-Views" / "webview2-diagnostics"
WEBVIEW2_POLICY_CHECK_REPORT_ROOT = Path("07_LOGS") / "Studio-Graph-Views" / "webview2-policy-checks"
WORKSPACE_TEMP_ACL_DIAGNOSTIC_REPORT_ROOT = (
    Path("07_LOGS") / "Studio-Graph-Views" / "workspace-temp-acl-cleanup-diagnostics"
)
PYWEBVIEW_MINIMAL_REPRO_REPORT_ROOT = (
    Path("07_LOGS") / "Studio-Graph-Views" / "pywebview-webview2-minimal-repro"
)
WEBVIEW2_RUNTIME_HOST_REMEDIATION_REPORT_ROOT = (
    Path("07_LOGS") / "Studio-Graph-Views" / "webview2-runtime-host-remediation"
)
WEBVIEW2_RUNTIME_REMEDIATION_EVIDENCE_REPORT_ROOT = (
    Path("07_LOGS") / "Studio-Graph-Views" / "webview2-runtime-remediation-evidence"
)


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _relative(vault: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(vault).as_posix()
    except ValueError:
        return str(path)


def _status(ok: bool, *, blocked: bool = False) -> str:
    if ok:
        return "VERIFIED"
    if blocked:
        return "BLOCKED"
    return "PARTIAL"


def _item(
    item_id: str,
    requirement: str,
    *,
    ok: bool,
    evidence: str,
    status: str | None = None,
) -> dict[str, Any]:
    return {
        "id": item_id,
        "requirement": requirement,
        "status": status or _status(ok),
        "ok": bool(ok),
        "evidence": evidence,
    }


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _latest_handoff_artifact(vault: Path) -> Path | None:
    root = vault / DEFAULT_HANDOFF_ROOT
    if not root.is_dir():
        return None
    candidates = [path for path in root.glob("*.md") if path.is_file()]
    if not candidates:
        candidates = [path for path in root.glob("*.json") if path.is_file()]
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def _latest_webview2_diagnostic_report(vault: Path) -> Path | None:
    root = vault / WEBVIEW2_DIAGNOSTIC_REPORT_ROOT
    if not root.is_dir():
        return None
    candidates = [path for path in root.glob("*.json") if path.is_file()]
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def _latest_webview2_policy_check_report(vault: Path) -> Path | None:
    root = vault / WEBVIEW2_POLICY_CHECK_REPORT_ROOT
    if not root.is_dir():
        return None
    candidates = [path for path in root.glob("*.json") if path.is_file()]
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def _latest_workspace_temp_acl_diagnostic_report(vault: Path) -> Path | None:
    root = vault / WORKSPACE_TEMP_ACL_DIAGNOSTIC_REPORT_ROOT
    if not root.is_dir():
        return None
    candidates = [path for path in root.glob("*.json") if path.is_file()]
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def _latest_pywebview_minimal_repro_report(vault: Path) -> Path | None:
    root = vault / PYWEBVIEW_MINIMAL_REPRO_REPORT_ROOT
    if not root.is_dir():
        return None
    candidates = [path for path in root.glob("*.json") if path.is_file()]
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def _latest_webview2_runtime_host_remediation_report(vault: Path) -> Path | None:
    root = vault / WEBVIEW2_RUNTIME_HOST_REMEDIATION_REPORT_ROOT
    if not root.is_dir():
        return None
    candidates = [path for path in root.glob("*.json") if path.is_file()]
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def _latest_webview2_runtime_remediation_evidence_report(vault: Path) -> Path | None:
    root = vault / WEBVIEW2_RUNTIME_REMEDIATION_EVIDENCE_REPORT_ROOT
    if not root.is_dir():
        return None
    candidates = [path for path in root.glob("*.json") if path.is_file()]
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def _latest_workspace_temp_acl_operator_handoff(vault: Path) -> Path | None:
    root = vault / WORKSPACE_TEMP_ACL_HANDOFF_ROOT
    if not root.is_dir():
        return None
    candidates = [path for path in root.glob("*.json") if path.is_file()]
    if not candidates:
        candidates = [path for path in root.glob("*.md") if path.is_file()]
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def _inspect_webview2_diagnostic_report(vault: Path) -> dict[str, Any]:
    selected = _latest_webview2_diagnostic_report(vault)
    if selected is None:
        return {
            "ok": False,
            "status": "NOT_FOUND",
            "path": None,
            "artifact_present": False,
            "report_type_valid": False,
            "next_recommended_pass": None,
            "reason": "No WebView2 diagnostic report was found.",
        }
    selected = selected.resolve()
    try:
        selected.relative_to(vault)
    except ValueError:
        return {
            "ok": False,
            "status": "OUTSIDE_VAULT",
            "path": str(selected),
            "artifact_present": False,
            "report_type_valid": False,
            "next_recommended_pass": None,
            "reason": "WebView2 diagnostic report must stay inside the vault workspace.",
        }
    try:
        payload = json.loads(selected.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "ok": False,
            "status": "UNREADABLE",
            "path": _relative(vault, selected),
            "artifact_present": True,
            "report_type_valid": False,
            "next_recommended_pass": None,
            "reason": f"WebView2 diagnostic report could not be read: {exc}",
        }
    authority = payload.get("authority") or {}
    report_type_valid = payload.get("surface") == "studio_packaged_app_webview2_diagnostic"
    authority_boundary = not any(
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
    ok = bool(report_type_valid and authority_boundary and payload.get("next_recommended_pass"))
    return {
        "ok": ok,
        "status": "VERIFIED" if ok else "PARTIAL",
        "path": _relative(vault, selected),
        "artifact_present": True,
        "report_type_valid": report_type_valid,
        "authority_boundary_present": authority_boundary,
        "report_status": payload.get("status"),
        "report_ok": bool(payload.get("ok")),
        "next_recommended_pass": payload.get("next_recommended_pass"),
        "checks": payload.get("checks") or [],
        "blockers": payload.get("blockers") or [],
        "reason": "Latest WebView2 diagnostic report checked.",
    }


def _inspect_webview2_policy_check_report(vault: Path) -> dict[str, Any]:
    selected = _latest_webview2_policy_check_report(vault)
    if selected is None:
        return {
            "ok": False,
            "status": "NOT_FOUND",
            "path": None,
            "artifact_present": False,
            "report_type_valid": False,
            "next_recommended_pass": None,
            "reason": "No WebView2 temp/policy check report was found.",
        }
    selected = selected.resolve()
    try:
        selected.relative_to(vault)
    except ValueError:
        return {
            "ok": False,
            "status": "OUTSIDE_VAULT",
            "path": str(selected),
            "artifact_present": False,
            "report_type_valid": False,
            "next_recommended_pass": None,
            "reason": "WebView2 temp/policy check report must stay inside the vault workspace.",
        }
    try:
        payload = json.loads(selected.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "ok": False,
            "status": "UNREADABLE",
            "path": _relative(vault, selected),
            "artifact_present": True,
            "report_type_valid": False,
            "next_recommended_pass": None,
            "reason": f"WebView2 temp/policy check report could not be read: {exc}",
        }
    authority = payload.get("authority") or {}
    report_type_valid = payload.get("surface") == "studio_packaged_app_webview2_policy_check"
    authority_boundary = not any(
        bool(authority.get(key))
        for key in (
            "mutates_temp_acl",
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
    ok = bool(report_type_valid and authority_boundary and payload.get("next_recommended_pass"))
    return {
        "ok": ok,
        "status": "VERIFIED" if ok else "PARTIAL",
        "path": _relative(vault, selected),
        "artifact_present": True,
        "report_type_valid": report_type_valid,
        "authority_boundary_present": authority_boundary,
        "report_status": payload.get("status"),
        "report_ok": bool(payload.get("ok")),
        "next_recommended_pass": payload.get("next_recommended_pass"),
        "checks": payload.get("checks") or [],
        "blockers": payload.get("blockers") or [],
        "reason": "Latest WebView2 temp/policy check report checked.",
    }


def _inspect_workspace_temp_acl_diagnostic_report(vault: Path) -> dict[str, Any]:
    selected = _latest_workspace_temp_acl_diagnostic_report(vault)
    if selected is None:
        return {
            "ok": False,
            "status": "NOT_FOUND",
            "path": None,
            "artifact_present": False,
            "report_type_valid": False,
            "next_recommended_pass": None,
            "reason": "No workspace temp ACL cleanup diagnostic report was found.",
        }
    selected = selected.resolve()
    try:
        selected.relative_to(vault)
    except ValueError:
        return {
            "ok": False,
            "status": "OUTSIDE_VAULT",
            "path": str(selected),
            "artifact_present": False,
            "report_type_valid": False,
            "next_recommended_pass": None,
            "reason": "Workspace temp ACL cleanup diagnostic report must stay inside the vault workspace.",
        }
    try:
        payload = json.loads(selected.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "ok": False,
            "status": "UNREADABLE",
            "path": _relative(vault, selected),
            "artifact_present": True,
            "report_type_valid": False,
            "next_recommended_pass": None,
            "reason": f"Workspace temp ACL cleanup diagnostic report could not be read: {exc}",
        }
    authority = payload.get("authority") or {}
    report_type_valid = payload.get("surface") == "studio_workspace_temp_acl_cleanup_diagnostic"
    authority_boundary = not any(
        bool(authority.get(key))
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
    ok = bool(report_type_valid and authority_boundary and payload.get("next_recommended_pass"))
    return {
        "ok": ok,
        "status": "VERIFIED" if ok else "PARTIAL",
        "path": _relative(vault, selected),
        "artifact_present": True,
        "report_type_valid": report_type_valid,
        "authority_boundary_present": authority_boundary,
        "report_status": payload.get("status"),
        "report_ok": bool(payload.get("ok")),
        "next_recommended_pass": payload.get("next_recommended_pass"),
        "checks": payload.get("checks") or [],
        "blockers": payload.get("blockers") or [],
        "reason": "Latest workspace temp ACL cleanup diagnostic report checked.",
    }


def _inspect_pywebview_minimal_repro_report(vault: Path) -> dict[str, Any]:
    selected = _latest_pywebview_minimal_repro_report(vault)
    if selected is None:
        return {
            "ok": False,
            "status": "NOT_FOUND",
            "path": None,
            "artifact_present": False,
            "report_type_valid": False,
            "next_recommended_pass": None,
            "reason": "No PyWebView WebView2 minimal repro report was found.",
        }
    selected = selected.resolve()
    try:
        selected.relative_to(vault)
    except ValueError:
        return {
            "ok": False,
            "status": "OUTSIDE_VAULT",
            "path": str(selected),
            "artifact_present": False,
            "report_type_valid": False,
            "next_recommended_pass": None,
            "reason": "PyWebView WebView2 minimal repro report must stay inside the vault workspace.",
        }
    try:
        payload = json.loads(selected.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "ok": False,
            "status": "UNREADABLE",
            "path": _relative(vault, selected),
            "artifact_present": True,
            "report_type_valid": False,
            "next_recommended_pass": None,
            "reason": f"PyWebView WebView2 minimal repro report could not be read: {exc}",
        }
    if payload.get("action") == "studio.pywebview-webview2-minimal-repro" and isinstance(payload.get("result"), dict):
        payload = payload["result"]
    authority = payload.get("authority") or {}
    report_type_valid = payload.get("surface") == "studio_pywebview_webview2_minimal_repro"
    authority_boundary = not any(
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
    source_probe = payload.get("source_probe") or {}
    visual_probe = payload.get("visual_probe") or {}
    source_runtime_error = (source_probe.get("launch") or {}).get("runtime_error") or {}
    visual_runtime_error = ((visual_probe.get("launch") or {}).get("runtime_error") or {})
    ok = bool(report_type_valid and authority_boundary and payload.get("next_recommended_pass"))
    return {
        "ok": ok,
        "status": "VERIFIED" if ok else "PARTIAL",
        "path": _relative(vault, selected),
        "artifact_present": True,
        "report_type_valid": report_type_valid,
        "authority_boundary_present": authority_boundary,
        "report_status": payload.get("status"),
        "report_ok": bool(payload.get("ok")),
        "source_probe_status": source_probe.get("status"),
        "source_runtime_error_status": source_runtime_error.get("status"),
        "source_runtime_blocked": bool(source_runtime_error.get("blocked")),
        "packaged_visual_probe_status": visual_probe.get("status"),
        "packaged_runtime_error_status": visual_runtime_error.get("status"),
        "packaged_runtime_blocked": bool(visual_runtime_error.get("blocked")),
        "next_recommended_pass": payload.get("next_recommended_pass"),
        "checks": payload.get("checks") or [],
        "blockers": payload.get("blockers") or [],
        "reason": "Latest PyWebView WebView2 minimal repro report checked.",
    }


def _inspect_webview2_runtime_host_remediation_report(vault: Path) -> dict[str, Any]:
    selected = _latest_webview2_runtime_host_remediation_report(vault)
    if selected is None:
        return {
            "ok": False,
            "status": "NOT_FOUND",
            "path": None,
            "artifact_present": False,
            "report_type_valid": False,
            "next_recommended_pass": None,
            "reason": "No WebView2 runtime host remediation report was found.",
        }
    selected = selected.resolve()
    try:
        selected.relative_to(vault)
    except ValueError:
        return {
            "ok": False,
            "status": "OUTSIDE_VAULT",
            "path": str(selected),
            "artifact_present": False,
            "report_type_valid": False,
            "next_recommended_pass": None,
            "reason": "WebView2 runtime host remediation report must stay inside the vault workspace.",
        }
    try:
        payload = json.loads(selected.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "ok": False,
            "status": "UNREADABLE",
            "path": _relative(vault, selected),
            "artifact_present": True,
            "report_type_valid": False,
            "next_recommended_pass": None,
            "reason": f"WebView2 runtime host remediation report could not be read: {exc}",
        }
    if payload.get("action") == "studio.webview2-runtime-host-remediation" and isinstance(payload.get("result"), dict):
        payload = payload["result"]
    authority = payload.get("authority") or {}
    report_type_valid = payload.get("surface") == "studio_webview2_runtime_host_remediation"
    authority_boundary = bool(authority.get("review_only")) and not any(
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
    handoff = payload.get("operator_handoff") or {}
    latest_minimal = payload.get("latest_minimal_repro") or {}
    required_actions = bool(handoff.get("required_external_actions"))
    acceptance_criteria = bool(handoff.get("acceptance_criteria"))
    rerun_commands = bool(handoff.get("minimal_repro_command")) and bool(handoff.get("packaged_visual_qa_command"))
    ok = bool(
        report_type_valid
        and authority_boundary
        and required_actions
        and acceptance_criteria
        and rerun_commands
        and payload.get("next_recommended_pass")
    )
    return {
        "ok": ok,
        "status": "VERIFIED" if ok else "PARTIAL",
        "path": _relative(vault, selected),
        "artifact_present": True,
        "report_type_valid": report_type_valid,
        "authority_boundary_present": authority_boundary,
        "required_actions_present": required_actions,
        "acceptance_criteria_present": acceptance_criteria,
        "rerun_commands_present": rerun_commands,
        "report_status": payload.get("status"),
        "report_ok": bool(payload.get("ok")),
        "source_runtime_error_status": latest_minimal.get("source_runtime_error_status"),
        "packaged_runtime_error_status": latest_minimal.get("packaged_runtime_error_status"),
        "next_recommended_pass": payload.get("next_recommended_pass"),
        "checks": payload.get("checks") or [],
        "blockers": payload.get("blockers") or [],
        "reason": "Latest WebView2 runtime host remediation report checked.",
    }


def _inspect_webview2_runtime_remediation_evidence_report(
    vault: Path,
    evidence_report_path: str | Path | None,
) -> dict[str, Any]:
    selected = Path(evidence_report_path) if evidence_report_path else _latest_webview2_runtime_remediation_evidence_report(vault)
    if selected is None:
        return {
            "ok": False,
            "status": "NOT_SUPPLIED",
            "path": None,
            "artifact_present": False,
            "report_type_valid": False,
            "authority_boundary_present": False,
            "operator_remediation_evidence_supplied": False,
            "remediation_effect_verified": False,
            "next_recommended_pass": None,
            "reason": "No WebView2 runtime remediation evidence report was supplied or found.",
        }
    if not selected.is_absolute():
        selected = vault / selected
    selected = selected.resolve()
    try:
        selected.relative_to(vault)
    except ValueError:
        return {
            "ok": False,
            "status": "OUTSIDE_VAULT",
            "path": str(selected),
            "artifact_present": False,
            "report_type_valid": False,
            "authority_boundary_present": False,
            "operator_remediation_evidence_supplied": False,
            "remediation_effect_verified": False,
            "next_recommended_pass": None,
            "reason": "WebView2 runtime remediation evidence report must stay inside the vault workspace.",
        }
    try:
        payload = json.loads(selected.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "ok": False,
            "status": "UNREADABLE",
            "path": _relative(vault, selected),
            "artifact_present": True,
            "report_type_valid": False,
            "authority_boundary_present": False,
            "operator_remediation_evidence_supplied": False,
            "remediation_effect_verified": False,
            "next_recommended_pass": None,
            "reason": f"WebView2 runtime remediation evidence report could not be read: {exc}",
        }
    if payload.get("action") == "studio.webview2-runtime-remediation-evidence" and isinstance(
        payload.get("result"),
        dict,
    ):
        payload = payload["result"]
    authority = payload.get("authority") or {}
    readiness = payload.get("readiness") or {}
    remediation = payload.get("remediation") or {}
    report_type_valid = (
        payload.get("surface") == "studio_webview2_runtime_remediation_evidence"
        or payload.get("report_type") == "webview2_runtime_remediation_evidence_intake"
    )
    authority_boundary = bool(authority.get("review_only")) and not any(
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
    operator_evidence_supplied = bool(readiness.get("operator_remediation_evidence_supplied"))
    remediation_effect_verified = bool(readiness.get("remediation_effect_verified"))
    ok = bool(report_type_valid and authority_boundary and operator_evidence_supplied)
    return {
        "ok": ok,
        "status": "VERIFIED" if ok else "PARTIAL",
        "path": _relative(vault, selected),
        "artifact_present": True,
        "report_type_valid": report_type_valid,
        "authority_boundary_present": authority_boundary,
        "operator_remediation_evidence_supplied": operator_evidence_supplied,
        "remediation_effect_verified": remediation_effect_verified,
        "remediation_status": remediation.get("status"),
        "operator": remediation.get("operator"),
        "evidence_reference": remediation.get("evidence_reference"),
        "report_status": payload.get("status"),
        "report_ok": bool(payload.get("ok")),
        "next_recommended_pass": payload.get("next_recommended_pass") or readiness.get("next_recommended_pass"),
        "checks": payload.get("checks") or [],
        "blockers": payload.get("blockers") or readiness.get("blockers") or [],
        "reason": "Latest WebView2 runtime remediation evidence report checked.",
    }


def _inspect_host_policy_handoff_artifact(
    vault: Path,
    handoff_path: str | Path | None,
) -> dict[str, Any]:
    selected = Path(handoff_path) if handoff_path else _latest_handoff_artifact(vault)
    if selected is None:
        return {
            "ok": False,
            "status": "NOT_FOUND",
            "path": None,
            "artifact_present": False,
            "review_only_boundary": False,
            "host_policy_blocker_referenced": False,
            "acceptance_criteria_present": False,
            "visual_qa_rerun_present": False,
            "authority_boundary_present": False,
            "reason": "No host-policy handoff artifact was supplied or found.",
        }
    if not selected.is_absolute():
        selected = vault / selected
    selected = selected.resolve()
    try:
        selected.relative_to(vault)
    except ValueError:
        return {
            "ok": False,
            "status": "OUTSIDE_VAULT",
            "path": str(selected),
            "artifact_present": False,
            "review_only_boundary": False,
            "host_policy_blocker_referenced": False,
            "acceptance_criteria_present": False,
            "visual_qa_rerun_present": False,
            "authority_boundary_present": False,
            "reason": "Host-policy handoff artifact must stay inside the vault workspace.",
        }
    if not selected.is_file():
        return {
            "ok": False,
            "status": "MISSING",
            "path": _relative(vault, selected),
            "artifact_present": False,
            "review_only_boundary": False,
            "host_policy_blocker_referenced": False,
            "acceptance_criteria_present": False,
            "visual_qa_rerun_present": False,
            "authority_boundary_present": False,
            "reason": "Host-policy handoff artifact path does not exist.",
        }

    text = selected.read_text(encoding="utf-8")
    lower_text = text.lower()
    review_only = "review-only" in lower_text
    host_policy_blocker = "windows application control" in lower_text
    acceptance_criteria = "acceptance criteria" in lower_text
    visual_qa_rerun = "packaged-app-visual-qa" in lower_text or "visual qa" in lower_text
    authority_boundary = (
        "does not mutate" in lower_text
        and "agent bus" in lower_text
        and "canonical" in lower_text
    )
    ok = all([review_only, host_policy_blocker, acceptance_criteria, visual_qa_rerun, authority_boundary])
    return {
        "ok": ok,
        "status": "VERIFIED" if ok else "PARTIAL",
        "path": _relative(vault, selected),
        "artifact_present": True,
        "review_only_boundary": review_only,
        "host_policy_blocker_referenced": host_policy_blocker,
        "acceptance_criteria_present": acceptance_criteria,
        "visual_qa_rerun_present": visual_qa_rerun,
        "authority_boundary_present": authority_boundary,
        "reason": "Host-policy handoff artifact checked.",
    }


def _inspect_workspace_temp_acl_operator_handoff_artifact(
    vault: Path,
    handoff_path: str | Path | None,
) -> dict[str, Any]:
    selected = Path(handoff_path) if handoff_path else _latest_workspace_temp_acl_operator_handoff(vault)
    if selected is None:
        return {
            "ok": False,
            "status": "NOT_FOUND",
            "path": None,
            "artifact_present": False,
            "report_type_valid": False,
            "review_only_boundary": False,
            "workspace_temp_blocker_referenced": False,
            "acceptance_criteria_present": False,
            "visual_qa_rerun_present": False,
            "authority_boundary_present": False,
            "next_recommended_pass": None,
            "reason": "No workspace temp ACL operator handoff artifact was supplied or found.",
        }
    if not selected.is_absolute():
        selected = vault / selected
    selected = selected.resolve()
    try:
        selected.relative_to(vault)
    except ValueError:
        return {
            "ok": False,
            "status": "OUTSIDE_VAULT",
            "path": str(selected),
            "artifact_present": False,
            "report_type_valid": False,
            "review_only_boundary": False,
            "workspace_temp_blocker_referenced": False,
            "acceptance_criteria_present": False,
            "visual_qa_rerun_present": False,
            "authority_boundary_present": False,
            "next_recommended_pass": None,
            "reason": "Workspace temp ACL handoff artifact must stay inside the vault workspace.",
        }
    if not selected.is_file():
        return {
            "ok": False,
            "status": "MISSING",
            "path": _relative(vault, selected),
            "artifact_present": False,
            "report_type_valid": False,
            "review_only_boundary": False,
            "workspace_temp_blocker_referenced": False,
            "acceptance_criteria_present": False,
            "visual_qa_rerun_present": False,
            "authority_boundary_present": False,
            "next_recommended_pass": None,
            "reason": "Workspace temp ACL handoff artifact path does not exist.",
        }

    text = selected.read_text(encoding="utf-8")
    payload: dict[str, Any] | None = None
    if selected.suffix.lower() == ".json":
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            payload = None

    lower_text = text.lower()
    if payload:
        authority = payload.get("authority") or {}
        report_type_valid = payload.get("handoff_type") == "pass10b_workspace_temp_acl_operator_handoff"
        review_only = bool(authority.get("review_only")) and "review-only" in lower_text
        workspace_temp_blocker = bool(payload.get("blocked_paths")) and "workspace" in lower_text and "temp" in lower_text
        acceptance_criteria = bool((payload.get("operator_handoff") or {}).get("acceptance_criteria"))
        visual_qa_rerun = "packaged-app-visual-qa" in lower_text or "visual qa" in lower_text
        authority_boundary = not any(
            bool(authority.get(key))
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
        next_pass = payload.get("next_recommended_pass")
    else:
        report_type_valid = "workspace temp acl operator handoff" in lower_text
        review_only = "review-only" in lower_text
        workspace_temp_blocker = "workspace temp" in lower_text and ("acl" in lower_text or "blocked" in lower_text)
        acceptance_criteria = "acceptance criteria" in lower_text
        visual_qa_rerun = "packaged-app-visual-qa" in lower_text or "visual qa" in lower_text
        authority_boundary = (
            "does not mutate temp acls" in lower_text
            and "does not delete stale temp artifacts" in lower_text
            and "agent bus" in lower_text
            and "canonical" in lower_text
        )
        next_pass = None

    ok = all([report_type_valid, review_only, workspace_temp_blocker, acceptance_criteria, visual_qa_rerun, authority_boundary])
    return {
        "ok": ok,
        "status": "VERIFIED" if ok else "PARTIAL",
        "path": _relative(vault, selected),
        "artifact_present": True,
        "report_type_valid": report_type_valid,
        "review_only_boundary": review_only,
        "workspace_temp_blocker_referenced": workspace_temp_blocker,
        "acceptance_criteria_present": acceptance_criteria,
        "visual_qa_rerun_present": visual_qa_rerun,
        "authority_boundary_present": authority_boundary,
        "next_recommended_pass": next_pass,
        "reason": "Workspace temp ACL operator handoff artifact checked.",
    }


def _inspect_native_screenshot_evidence_report(
    vault: Path,
    evidence_report_path: str | Path | None,
) -> dict[str, Any]:
    if not evidence_report_path:
        return {
            "ok": False,
            "status": "NOT_SUPPLIED",
            "path": None,
            "artifact_present": False,
            "report_type_valid": False,
            "authority_boundary_present": False,
            "automated_qa_stays_incomplete": True,
            "can_close_native_visual_proof": False,
            "readiness": {},
            "screenshot": {},
            "reason": "No saved native screenshot evidence report was supplied.",
        }
    selected = Path(evidence_report_path)
    if not selected.is_absolute():
        selected = vault / selected
    selected = selected.resolve()
    try:
        selected.relative_to(vault)
    except ValueError:
        return {
            "ok": False,
            "status": "OUTSIDE_VAULT",
            "path": str(selected),
            "artifact_present": False,
            "report_type_valid": False,
            "authority_boundary_present": False,
            "automated_qa_stays_incomplete": False,
            "can_close_native_visual_proof": False,
            "readiness": {},
            "screenshot": {},
            "reason": "Native screenshot evidence report must stay inside the vault workspace.",
        }
    if not selected.is_file():
        return {
            "ok": False,
            "status": "MISSING",
            "path": _relative(vault, selected),
            "artifact_present": False,
            "report_type_valid": False,
            "authority_boundary_present": False,
            "automated_qa_stays_incomplete": False,
            "can_close_native_visual_proof": False,
            "readiness": {},
            "screenshot": {},
            "reason": "Native screenshot evidence report path does not exist.",
        }
    try:
        payload = json.loads(selected.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {
            "ok": False,
            "status": "INVALID_JSON",
            "path": _relative(vault, selected),
            "artifact_present": True,
            "report_type_valid": False,
            "authority_boundary_present": False,
            "automated_qa_stays_incomplete": False,
            "can_close_native_visual_proof": False,
            "readiness": {},
            "screenshot": {},
            "reason": f"Native screenshot evidence report is not valid JSON: {exc}",
        }

    readiness = payload.get("readiness") or {}
    authority_note = str(payload.get("authority_note") or "").lower()
    report_type_valid = payload.get("report_type") == "pass10b_native_screenshot_evidence_intake"
    can_close = bool(readiness.get("can_close_pass10b_native_visual_proof"))
    automated_complete = bool(readiness.get("automated_packaged_visual_qa_complete"))
    authority_boundary = (
        "supplemental" in authority_note
        and "cannot complete automated packaged visual qa" in authority_note
        and "mutate host policy" in authority_note
        and "agent bus" in authority_note
        and "canonical state" in authority_note
    )
    automated_stays_incomplete = not automated_complete and not can_close
    ok = report_type_valid and authority_boundary and automated_stays_incomplete
    return {
        "ok": ok,
        "status": "VERIFIED" if ok else "PARTIAL",
        "path": _relative(vault, selected),
        "artifact_present": True,
        "report_type_valid": report_type_valid,
        "authority_boundary_present": authority_boundary,
        "automated_qa_stays_incomplete": automated_stays_incomplete,
        "can_close_native_visual_proof": can_close,
        "readiness": readiness,
        "screenshot": payload.get("screenshot") or {},
        "report_status": payload.get("status"),
        "report_ok": bool(payload.get("ok")),
        "reason": "Saved native screenshot evidence report checked.",
    }


def _check_named(report: dict[str, Any], name: str) -> bool:
    for item in report.get("checks") or []:
        if item.get("name") == name:
            return bool(item.get("ok"))
    return False


def _inspect_packaged_visual_qa_report(
    vault: Path,
    visual_qa_report_path: str | Path | None,
) -> dict[str, Any]:
    if not visual_qa_report_path:
        return {
            "ok": False,
            "status": "NOT_SUPPLIED",
            "path": None,
            "artifact_present": False,
            "report_type_valid": False,
            "host_policy_allows_launch": False,
            "native_visual_qa_complete": False,
            "executable_path": None,
            "executable_path_valid": False,
            "authority_boundary_present": False,
            "reason": "No saved packaged visual-QA report was supplied.",
        }
    selected = Path(visual_qa_report_path)
    if not selected.is_absolute():
        selected = vault / selected
    selected = selected.resolve()
    try:
        selected.relative_to(vault)
    except ValueError:
        return {
            "ok": False,
            "status": "OUTSIDE_VAULT",
            "path": str(selected),
            "artifact_present": False,
            "report_type_valid": False,
            "host_policy_allows_launch": False,
            "native_visual_qa_complete": False,
            "executable_path": None,
            "executable_path_valid": False,
            "authority_boundary_present": False,
            "reason": "Packaged visual-QA report must stay inside the vault workspace.",
        }
    if not selected.is_file():
        return {
            "ok": False,
            "status": "MISSING",
            "path": _relative(vault, selected),
            "artifact_present": False,
            "report_type_valid": False,
            "host_policy_allows_launch": False,
            "native_visual_qa_complete": False,
            "executable_path": None,
            "executable_path_valid": False,
            "authority_boundary_present": False,
            "reason": "Packaged visual-QA report path does not exist.",
        }
    try:
        payload = json.loads(selected.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {
            "ok": False,
            "status": "INVALID_JSON",
            "path": _relative(vault, selected),
            "artifact_present": True,
            "report_type_valid": False,
            "host_policy_allows_launch": False,
            "native_visual_qa_complete": False,
            "executable_path": None,
            "executable_path_valid": False,
            "authority_boundary_present": False,
            "reason": f"Packaged visual-QA report is not valid JSON: {exc}",
        }

    executable = payload.get("executable") or {}
    executable_path = executable.get("path")
    executable_path_valid = False
    executable_path_reason = "not_supplied"
    if executable_path:
        candidate = Path(str(executable_path))
        if not candidate.is_absolute():
            candidate = vault / candidate
        try:
            candidate.resolve().relative_to(vault)
        except ValueError:
            executable_path_reason = "outside_vault"
        else:
            executable_path_valid = True
            executable_path_reason = "vault_scoped"

    screenshot = payload.get("screenshot") or {}
    visual = screenshot.get("visual_verification") or {}
    studio_content_sentinel = screenshot.get("studio_content_sentinel") or {}
    launch = payload.get("launch") or {}
    runtime_error = launch.get("runtime_error") or {}
    termination = payload.get("termination") or {}
    authority = payload.get("authority") or {}
    host_policy = launch.get("host_policy") or payload.get("host_policy") or {}
    forbidden_authority = [
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
    report_type_valid = (
        payload.get("surface") == "studio_packaged_app_visual_qa"
        and payload.get("model_version") == "studio.packaged_app_visual_qa.v1"
    )
    host_allows = _check_named(payload, "host_policy_allows_launch") and not bool(
        host_policy.get("blocked_by_windows_application_control")
    )
    native_visual_complete = all(
        [
            bool(payload.get("ok")),
            payload.get("status") == "packaged_app_visual_qa_complete",
            bool(launch.get("started")),
            bool(launch.get("process_alive_before_capture")),
            bool(screenshot.get("exists")),
            int(screenshot.get("size_bytes") or 0) > 1000,
            bool(visual.get("ok")),
            bool(studio_content_sentinel.get("ok")),
            _check_named(payload, "window_capture_ok"),
            _check_named(payload, "screenshot_nonblank"),
            _check_named(payload, "screenshot_studio_content_sentinel"),
            _check_named(payload, "window_bounds_valid"),
            bool(termination.get("terminated")),
            _check_named(payload, "no_markdown_writes"),
            _check_named(payload, "no_approval_artifact_writes"),
        ]
    )
    authority_boundary = not any(bool(authority.get(key)) for key in forbidden_authority)
    ok = report_type_valid and host_allows and native_visual_complete and authority_boundary
    return {
        "ok": ok,
        "status": "VERIFIED" if ok else "PARTIAL",
        "path": _relative(vault, selected),
        "artifact_present": True,
        "report_type_valid": report_type_valid,
        "host_policy_allows_launch": host_allows,
        "native_visual_qa_complete": native_visual_complete,
        "authority_boundary_present": authority_boundary,
        "report_status": payload.get("status"),
        "report_ok": bool(payload.get("ok")),
        "executable": executable,
        "executable_path": executable_path,
        "executable_path_valid": executable_path_valid,
        "executable_path_reason": executable_path_reason,
        "screenshot": screenshot,
        "studio_content_sentinel_verified": bool(studio_content_sentinel.get("ok")) and _check_named(payload, "screenshot_studio_content_sentinel"),
        "host_policy": host_policy,
        "runtime_error": runtime_error,
        "reason": "Saved packaged visual-QA report checked.",
    }


def build_pass10b_visual_proof_completion_audit(
    vault_root: str | Path,
    *,
    probe_native_host_policy: bool = False,
    native_probe_settle_seconds: float = 1.0,
    native_probe_window_timeout_seconds: float = 1.0,
    native_probe_terminate_timeout_seconds: float = 1.0,
    native_screenshot_path: str | Path | None = None,
    native_screenshot_source: str = "unknown",
    native_evidence_report_path: str | Path | None = None,
    packaged_visual_qa_report_path: str | Path | None = None,
    host_policy_handoff_path: str | Path | None = None,
    workspace_temp_handoff_path: str | Path | None = None,
    webview2_remediation_evidence_path: str | Path | None = None,
) -> dict[str, Any]:
    """Map Pass 10B visual-proof completion criteria to concrete repo evidence."""

    vault = _vault_path(vault_root)
    browser_evidence = vault / BROWSER_NONBLANK_EVIDENCE
    browser_visual = analyze_png_nonblank(
        browser_evidence,
        min_unique_colors=8,
        max_dominant_ratio=0.995,
    )
    packaged_visual_qa_report = _inspect_packaged_visual_qa_report(vault, packaged_visual_qa_report_path)
    host_policy_probe_executable_path = None
    host_policy_probe_executable_source = "default_packaging_proof"
    if (
        packaged_visual_qa_report_path
        and packaged_visual_qa_report.get("executable_path")
        and packaged_visual_qa_report.get("executable_path_valid")
    ):
        host_policy_probe_executable_path = packaged_visual_qa_report.get("executable_path")
        host_policy_probe_executable_source = "packaged_visual_qa_report"
    host_policy = build_packaged_app_host_policy_unblock_readiness(
        vault,
        executable_path=host_policy_probe_executable_path,
        probe_launch=probe_native_host_policy,
        settle_seconds=native_probe_settle_seconds,
        window_timeout_seconds=native_probe_window_timeout_seconds,
        terminate_timeout_seconds=native_probe_terminate_timeout_seconds,
    )
    host_readiness = host_policy.get("readiness") or {}
    webview2_diagnostic_report = _inspect_webview2_diagnostic_report(vault)
    webview2_policy_check_report = _inspect_webview2_policy_check_report(vault)
    workspace_temp_acl_diagnostic_report = _inspect_workspace_temp_acl_diagnostic_report(vault)
    pywebview_minimal_repro_report = _inspect_pywebview_minimal_repro_report(vault)
    webview2_runtime_host_remediation_report = _inspect_webview2_runtime_host_remediation_report(vault)
    webview2_runtime_remediation_evidence_report = _inspect_webview2_runtime_remediation_evidence_report(
        vault,
        webview2_remediation_evidence_path,
    )
    native_visual_complete = bool(host_readiness.get("native_visual_qa_complete")) or bool(
        packaged_visual_qa_report.get("native_visual_qa_complete")
    )
    host_policy_allows_launch = bool(host_readiness.get("host_policy_allows_launch")) or bool(
        packaged_visual_qa_report.get("host_policy_allows_launch")
    )
    supplemental_native_evidence: dict[str, Any] | None = None
    if native_screenshot_path:
        supplemental_native_evidence = build_pass10b_native_screenshot_evidence_intake(
            vault,
            screenshot_path=native_screenshot_path,
            declared_source=native_screenshot_source,
        )
    saved_native_evidence_report = _inspect_native_screenshot_evidence_report(vault, native_evidence_report_path)
    supplemental_readiness = (
        (supplemental_native_evidence or {}).get("readiness")
        or saved_native_evidence_report.get("readiness")
        or {}
    )
    supplemental_native_verified = bool(supplemental_readiness.get("supplemental_native_screenshot_evidence_verified"))
    handoff_evidence = _inspect_host_policy_handoff_artifact(vault, host_policy_handoff_path)
    workspace_temp_handoff_evidence = _inspect_workspace_temp_acl_operator_handoff_artifact(
        vault,
        workspace_temp_handoff_path,
    )

    checklist = [
        _item(
            "pass10b_graph_settings_tests_present",
            "Focused Pass 10B graph settings regression surface exists.",
            ok=(vault / PASS10B_TEST_PATH).is_file(),
            evidence=_relative(vault, vault / PASS10B_TEST_PATH),
        ),
        _item(
            "desktop_shell_route_tests_present",
            "Desktop shell/static graph route regression surface exists.",
            ok=(vault / DESKTOP_SHELL_TEST_PATH).is_file(),
            evidence=_relative(vault, vault / DESKTOP_SHELL_TEST_PATH),
        ),
        _item(
            "browser_graph_route_nonblank_verified",
            "Browser graph-route visual evidence is a nonblank PNG.",
            ok=bool(browser_visual.get("ok")),
            evidence=(
                f"{_relative(vault, browser_evidence)}; "
                f"unique_color_count={browser_visual.get('unique_color_count')}; "
                f"dominant_color_ratio={browser_visual.get('dominant_color_ratio')}; "
                f"reason={browser_visual.get('reason')}"
            ),
        ),
        _item(
            "packaged_visual_qa_host_policy_readiness_available",
            "Packaged/native visual QA host-policy unblock readiness is available.",
            ok=True,
            evidence="runtime/studio/packaged_app_host_policy_unblock.py",
        ),
        _item(
            "native_host_policy_probe_performed",
            "Native packaged host-policy launch probe or saved packaged visual-QA report has been checked for this audit.",
            ok=bool(host_readiness.get("host_policy_probe_performed")) or bool(packaged_visual_qa_report.get("ok")),
            evidence=(
                f"probe_native_host_policy={probe_native_host_policy}; "
                f"settle_seconds={native_probe_settle_seconds}; "
                f"window_timeout_seconds={native_probe_window_timeout_seconds}; "
                f"terminate_timeout_seconds={native_probe_terminate_timeout_seconds}; "
                f"host_policy_probe_executable_source={host_policy_probe_executable_source}; "
                f"host_policy_probe_executable_path={host_policy_probe_executable_path or 'default'}; "
                f"packaged_visual_qa_report_path={packaged_visual_qa_report_path or 'not_supplied'}; "
                f"packaged_visual_qa_report_status={packaged_visual_qa_report.get('status')}"
            ),
            status=_status(
                bool(host_readiness.get("host_policy_probe_performed")) or bool(packaged_visual_qa_report.get("ok"))
            ),
        ),
        _item(
            "native_host_policy_allows_launch",
            "Packaged executable can launch under current host policy.",
            ok=host_policy_allows_launch,
            evidence=f"host_policy_status={(host_policy.get('host_policy') or {}).get('status')}",
            status=_status(host_policy_allows_launch, blocked=probe_native_host_policy),
        ),
        _item(
            "native_packaged_visual_qa_complete",
            "Native packaged visual QA captured a real screenshot and passed the nonblank gate.",
            ok=native_visual_complete,
            evidence=(
                f"host_policy_readiness_status={host_policy.get('status')}; "
                f"packaged_visual_qa_report_status={packaged_visual_qa_report.get('report_status') or 'not_supplied'}"
            ),
            status=_status(native_visual_complete, blocked=True),
        ),
        _item(
            "packaged_visual_qa_saved_report_valid",
            "Optional saved packaged visual-QA report proves native launch, native screenshot capture, nonblank pixels, termination, and no forbidden writes.",
            ok=bool(packaged_visual_qa_report.get("ok")),
            evidence=(
                f"path={packaged_visual_qa_report.get('path') or 'not_supplied'}; "
                f"report_type_valid={packaged_visual_qa_report.get('report_type_valid')}; "
                f"executable_path={packaged_visual_qa_report.get('executable_path') or 'not_supplied'}; "
                f"executable_path_valid={packaged_visual_qa_report.get('executable_path_valid')}; "
                f"host_policy_allows_launch={packaged_visual_qa_report.get('host_policy_allows_launch')}; "
                f"native_visual_qa_complete={packaged_visual_qa_report.get('native_visual_qa_complete')}; "
                f"runtime_error_status={(packaged_visual_qa_report.get('runtime_error') or {}).get('status')}"
            ),
            status=packaged_visual_qa_report.get("status"),
        ),
        _item(
            "webview2_diagnostic_report_checked",
            "Latest WebView2 diagnostic report is checked when available.",
            ok=bool(webview2_diagnostic_report.get("ok")),
            evidence=(
                f"path={webview2_diagnostic_report.get('path') or 'not_found'}; "
                f"status={webview2_diagnostic_report.get('report_status')}; "
                f"next={webview2_diagnostic_report.get('next_recommended_pass')}"
            ),
            status=webview2_diagnostic_report.get("status"),
        ),
        _item(
            "webview2_policy_check_report_checked",
            "Latest WebView2 temp/policy check report is checked when available.",
            ok=bool(webview2_policy_check_report.get("ok")),
            evidence=(
                f"path={webview2_policy_check_report.get('path') or 'not_found'}; "
                f"status={webview2_policy_check_report.get('report_status')}; "
                f"next={webview2_policy_check_report.get('next_recommended_pass')}"
            ),
            status=webview2_policy_check_report.get("status"),
        ),
        _item(
            "workspace_temp_acl_diagnostic_report_checked",
            "Latest workspace temp ACL cleanup diagnostic report is checked when available.",
            ok=bool(workspace_temp_acl_diagnostic_report.get("ok")),
            evidence=(
                f"path={workspace_temp_acl_diagnostic_report.get('path') or 'not_found'}; "
                f"status={workspace_temp_acl_diagnostic_report.get('report_status')}; "
                f"next={workspace_temp_acl_diagnostic_report.get('next_recommended_pass')}"
            ),
            status=workspace_temp_acl_diagnostic_report.get("status"),
        ),
        _item(
            "pywebview_webview2_minimal_repro_report_checked",
            "Latest minimal PyWebView/WebView2 repro report is checked when available.",
            ok=bool(pywebview_minimal_repro_report.get("ok")),
            evidence=(
                f"path={pywebview_minimal_repro_report.get('path') or 'not_found'}; "
                f"status={pywebview_minimal_repro_report.get('report_status')}; "
                f"source_runtime={pywebview_minimal_repro_report.get('source_runtime_error_status')}; "
                f"packaged_runtime={pywebview_minimal_repro_report.get('packaged_runtime_error_status')}; "
                f"next={pywebview_minimal_repro_report.get('next_recommended_pass')}"
            ),
            status=pywebview_minimal_repro_report.get("status"),
        ),
        _item(
            "webview2_runtime_host_remediation_report_checked",
            "Latest WebView2 runtime host remediation handoff/report is checked when available.",
            ok=bool(webview2_runtime_host_remediation_report.get("ok")),
            evidence=(
                f"path={webview2_runtime_host_remediation_report.get('path') or 'not_found'}; "
                f"status={webview2_runtime_host_remediation_report.get('report_status')}; "
                f"source_runtime={webview2_runtime_host_remediation_report.get('source_runtime_error_status')}; "
                f"packaged_runtime={webview2_runtime_host_remediation_report.get('packaged_runtime_error_status')}; "
                f"next={webview2_runtime_host_remediation_report.get('next_recommended_pass')}"
            ),
            status=webview2_runtime_host_remediation_report.get("status"),
        ),
        _item(
            "webview2_runtime_host_remediation_review_only",
            "WebView2 runtime host remediation handoff is review-only and preserves authority boundaries.",
            ok=bool(webview2_runtime_host_remediation_report.get("ok")),
            evidence=(
                f"authority_boundary_present={webview2_runtime_host_remediation_report.get('authority_boundary_present')}; "
                f"required_actions_present={webview2_runtime_host_remediation_report.get('required_actions_present')}; "
                f"acceptance_criteria_present={webview2_runtime_host_remediation_report.get('acceptance_criteria_present')}; "
                f"rerun_commands_present={webview2_runtime_host_remediation_report.get('rerun_commands_present')}"
            ),
            status=webview2_runtime_host_remediation_report.get("status"),
        ),
        _item(
            "webview2_runtime_remediation_evidence_checked",
            "Latest WebView2 runtime remediation evidence intake was checked when available.",
            ok=bool(webview2_runtime_remediation_evidence_report.get("artifact_present")),
            evidence=(
                f"path={webview2_runtime_remediation_evidence_report.get('path') or 'not_supplied'}; "
                f"status={webview2_runtime_remediation_evidence_report.get('report_status')}; "
                f"remediation_status={webview2_runtime_remediation_evidence_report.get('remediation_status')}; "
                f"next={webview2_runtime_remediation_evidence_report.get('next_recommended_pass')}"
            ),
            status=webview2_runtime_remediation_evidence_report.get("status"),
        ),
        _item(
            "webview2_runtime_remediation_evidence_supplied",
            "Operator/admin WebView2 runtime remediation evidence was supplied before rerunning minimal repro.",
            ok=bool(webview2_runtime_remediation_evidence_report.get("ok")),
            evidence=(
                "operator_remediation_evidence_supplied="
                f"{webview2_runtime_remediation_evidence_report.get('operator_remediation_evidence_supplied')}; "
                f"operator={webview2_runtime_remediation_evidence_report.get('operator')}; "
                f"evidence_reference={webview2_runtime_remediation_evidence_report.get('evidence_reference')}; "
                "remediation_effect_verified="
                f"{webview2_runtime_remediation_evidence_report.get('remediation_effect_verified')}"
            ),
            status=webview2_runtime_remediation_evidence_report.get("status"),
        ),
        _item(
            "webview2_runtime_remediation_evidence_review_only",
            "WebView2 runtime remediation evidence intake preserves review-only authority boundaries.",
            ok=bool(webview2_runtime_remediation_evidence_report.get("authority_boundary_present")),
            evidence=(
                "authority_boundary_present="
                f"{webview2_runtime_remediation_evidence_report.get('authority_boundary_present')}; "
                f"report_type_valid={webview2_runtime_remediation_evidence_report.get('report_type_valid')}"
            ),
            status=webview2_runtime_remediation_evidence_report.get("status"),
        ),
        _item(
            "workspace_temp_acl_operator_handoff_artifact_checked",
            "Workspace temp ACL operator handoff artifact was checked when required.",
            ok=bool(workspace_temp_handoff_evidence.get("artifact_present")),
            evidence=(
                f"path={workspace_temp_handoff_evidence.get('path') or 'not_found'}; "
                f"status={workspace_temp_handoff_evidence.get('status')}; "
                f"next={workspace_temp_handoff_evidence.get('next_recommended_pass')}"
            ),
            status=workspace_temp_handoff_evidence.get("status"),
        ),
        _item(
            "workspace_temp_acl_operator_handoff_review_only",
            "Workspace temp ACL operator handoff is review-only and preserves authority boundaries.",
            ok=bool(workspace_temp_handoff_evidence.get("ok")),
            evidence=(
                f"review_only_boundary={workspace_temp_handoff_evidence.get('review_only_boundary')}; "
                f"authority_boundary_present={workspace_temp_handoff_evidence.get('authority_boundary_present')}; "
                f"workspace_temp_blocker_referenced={workspace_temp_handoff_evidence.get('workspace_temp_blocker_referenced')}"
            ),
            status=workspace_temp_handoff_evidence.get("status"),
        ),
        _item(
            "host_policy_unblock_handoff_artifact_checked",
            "Durable host-policy unblock handoff artifact was checked when available.",
            ok=bool(handoff_evidence.get("artifact_present")),
            evidence=f"path={handoff_evidence.get('path') or 'not_found'}; status={handoff_evidence.get('status')}",
            status=handoff_evidence.get("status"),
        ),
        _item(
            "host_policy_unblock_handoff_review_only",
            "Host-policy unblock handoff is review-only and preserves authority boundaries.",
            ok=bool(handoff_evidence.get("ok")),
            evidence=(
                f"review_only_boundary={handoff_evidence.get('review_only_boundary')}; "
                f"authority_boundary_present={handoff_evidence.get('authority_boundary_present')}"
            ),
            status=handoff_evidence.get("status"),
        ),
        _item(
            "supplemental_native_screenshot_evidence_checked",
            "Optional supplied native screenshot evidence was checked if provided.",
            ok=(
                (not native_screenshot_path and not native_evidence_report_path)
                or supplemental_native_evidence is not None
                or bool(saved_native_evidence_report.get("artifact_present"))
            ),
            evidence=(
                f"native_screenshot_path={native_screenshot_path or 'not_supplied'}; "
                f"native_evidence_report_path={native_evidence_report_path or 'not_supplied'}; "
                f"status={(supplemental_native_evidence or {}).get('status') or saved_native_evidence_report.get('status')}"
            ),
        ),
        _item(
            "supplemental_native_screenshot_evidence_report_valid",
            "Optional saved native screenshot evidence report is the expected supplemental evidence type and preserves the non-completion boundary.",
            ok=bool(saved_native_evidence_report.get("ok")),
            evidence=(
                f"path={saved_native_evidence_report.get('path') or 'not_supplied'}; "
                f"report_type_valid={saved_native_evidence_report.get('report_type_valid')}; "
                f"automated_qa_stays_incomplete={saved_native_evidence_report.get('automated_qa_stays_incomplete')}"
            ),
            status=saved_native_evidence_report.get("status"),
        ),
        _item(
            "supplemental_native_screenshot_evidence_verified",
            "Optional supplied native screenshot evidence is nonblank and declared as native packaged-window evidence.",
            ok=supplemental_native_verified,
            evidence=(
                f"native_screenshot_source={native_screenshot_source}; "
                f"saved_report_source={(saved_native_evidence_report.get('screenshot') or {}).get('declared_source')}; "
                f"status={(supplemental_native_evidence or {}).get('status') or saved_native_evidence_report.get('report_status') or 'not_supplied'}"
            ),
            status=(
                "NOT_SUPPLIED"
                if not native_screenshot_path and not native_evidence_report_path
                else _status(supplemental_native_verified)
            ),
        ),
        _item(
            "supplemental_evidence_does_not_complete_automated_qa",
            "Supplemental evidence cannot close automated packaged visual QA.",
            ok=not bool(supplemental_readiness.get("can_close_pass10b_native_visual_proof")),
            evidence=(
                "can_close_pass10b_native_visual_proof="
                f"{supplemental_readiness.get('can_close_pass10b_native_visual_proof')}"
            ),
        ),
        _item(
            "no_authority_expansion",
            "Audit did not grant host policy, signing, installer, approval, Agent Bus, provider, connector, or canonical authority.",
            ok=not any((host_policy.get("authority") or {}).get(key) for key in [
                "mutates_host_policy",
                "signs_executable",
                "allowlists_executable",
                "writes_installer",
                "writes_host_startup",
                "executes_approval_decisions",
                "provider_calls_allowed",
                "connector_calls_allowed",
                "writes_agent_bus_tasks",
                "canonical_mutation_allowed",
            ]),
            evidence="host-policy readiness authority flags all denied",
        ),
    ]

    required_ids = {
        "pass10b_graph_settings_tests_present",
        "desktop_shell_route_tests_present",
        "browser_graph_route_nonblank_verified",
        "packaged_visual_qa_host_policy_readiness_available",
        "native_host_policy_probe_performed",
        "native_host_policy_allows_launch",
        "native_packaged_visual_qa_complete",
        "supplemental_evidence_does_not_complete_automated_qa",
        "no_authority_expansion",
    }
    if not host_policy_allows_launch:
        required_ids.add("host_policy_unblock_handoff_review_only")
    if native_evidence_report_path:
        required_ids.add("supplemental_native_screenshot_evidence_report_valid")
    if packaged_visual_qa_report_path:
        required_ids.add("packaged_visual_qa_saved_report_valid")
    packaged_runtime_blocked = bool((packaged_visual_qa_report.get("runtime_error") or {}).get("blocked"))
    if packaged_runtime_blocked and webview2_diagnostic_report.get("artifact_present"):
        required_ids.add("webview2_diagnostic_report_checked")
    if (
        packaged_runtime_blocked
        and webview2_diagnostic_report.get("next_recommended_pass")
        == "pass10b-system-temp-permission-or-webview2-policy-check"
        and webview2_policy_check_report.get("artifact_present")
    ):
        required_ids.add("webview2_policy_check_report_checked")
    if (
        packaged_runtime_blocked
        and webview2_policy_check_report.get("next_recommended_pass")
        == "pass10b-workspace-temp-acl-cleanup-diagnostic"
        and workspace_temp_acl_diagnostic_report.get("artifact_present")
    ):
        required_ids.add("workspace_temp_acl_diagnostic_report_checked")
    if (
        packaged_runtime_blocked
        and workspace_temp_acl_diagnostic_report.get("next_recommended_pass")
        in {
            "pass10b-workspace-temp-acl-operator-handoff",
            "pass10b-workspace-temp-stale-artifact-operator-handoff",
        }
    ):
        required_ids.add("workspace_temp_acl_operator_handoff_review_only")
    if (
        packaged_runtime_blocked
        and (
            webview2_policy_check_report.get("next_recommended_pass")
            == "pass10b-pywebview-webview2-minimal-repro"
            or workspace_temp_acl_diagnostic_report.get("next_recommended_pass")
            == "pass10b-pywebview-webview2-minimal-repro"
        )
        and pywebview_minimal_repro_report.get("artifact_present")
    ):
        required_ids.add("pywebview_webview2_minimal_repro_report_checked")
    if (
        packaged_runtime_blocked
        and pywebview_minimal_repro_report.get("next_recommended_pass")
        == "pass10b-webview2-runtime-host-remediation"
        and webview2_runtime_host_remediation_report.get("artifact_present")
    ):
        required_ids.add("webview2_runtime_host_remediation_review_only")
    if (
        packaged_runtime_blocked
        and webview2_runtime_host_remediation_report.get("next_recommended_pass")
        == "operator-remediate-webview2-runtime-then-pass10b-minimal-repro-rerun"
    ):
        required_ids.add("webview2_runtime_remediation_evidence_supplied")
        if webview2_runtime_remediation_evidence_report.get("artifact_present"):
            required_ids.add("webview2_runtime_remediation_evidence_review_only")
    missing = [item for item in checklist if item["id"] in required_ids and not item["ok"]]
    complete = not missing
    status = "COMPLETE / VERIFIED" if complete else "PARTIAL / BLOCKED_NATIVE_PACKAGED_VISUAL_QA"
    webview2_next_pass = webview2_diagnostic_report.get("next_recommended_pass")
    webview2_policy_next_pass = webview2_policy_check_report.get("next_recommended_pass")
    workspace_temp_acl_next_pass = workspace_temp_acl_diagnostic_report.get("next_recommended_pass")
    workspace_temp_handoff_next_pass = workspace_temp_handoff_evidence.get("next_recommended_pass")
    pywebview_minimal_next_pass = pywebview_minimal_repro_report.get("next_recommended_pass")
    webview2_remediation_next_pass = webview2_runtime_host_remediation_report.get("next_recommended_pass")
    webview2_remediation_evidence_next_pass = webview2_runtime_remediation_evidence_report.get("next_recommended_pass")
    next_pass = (
        "phase10-studio-product-hardening-closeout"
        if complete
        else (
            str(
                workspace_temp_handoff_next_pass
                if (
                    workspace_temp_acl_next_pass
                    in {
                        "pass10b-workspace-temp-acl-operator-handoff",
                        "pass10b-workspace-temp-stale-artifact-operator-handoff",
                    }
                    and workspace_temp_handoff_evidence.get("ok")
                    and workspace_temp_handoff_next_pass
                )
                else workspace_temp_acl_next_pass
                if (
                    webview2_policy_next_pass == "pass10b-workspace-temp-acl-cleanup-diagnostic"
                    and workspace_temp_acl_diagnostic_report.get("artifact_present")
                )
                else webview2_remediation_evidence_next_pass
                if (
                    webview2_remediation_next_pass
                    == "operator-remediate-webview2-runtime-then-pass10b-minimal-repro-rerun"
                    and webview2_runtime_remediation_evidence_report.get("ok")
                    and webview2_remediation_evidence_next_pass
                )
                else webview2_remediation_next_pass
                if (
                    webview2_runtime_host_remediation_report.get("ok")
                    and webview2_remediation_next_pass
                )
                else pywebview_minimal_next_pass
                if (
                    (
                        webview2_policy_next_pass == "pass10b-pywebview-webview2-minimal-repro"
                        or workspace_temp_acl_next_pass == "pass10b-pywebview-webview2-minimal-repro"
                    )
                    and pywebview_minimal_repro_report.get("artifact_present")
                    and pywebview_minimal_next_pass
                )
                else webview2_policy_next_pass
                if (
                    webview2_next_pass == "pass10b-system-temp-permission-or-webview2-policy-check"
                    and webview2_policy_check_report.get("artifact_present")
                )
                else (webview2_next_pass or "pass10b-webview2-runtime-diagnostic")
            )
            if packaged_runtime_blocked
            else (
                "pass10b-native-visual-qa-rerun-after-host-policy-unblock"
                if host_policy_allows_launch
                else "pass10b-native-host-policy-unblock"
            )
        )
    )

    return {
        "ok": complete,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "status": status,
        "objective": "continue development on the pass 10b expansion pack",
        "success_criteria": [
            "Browser/static graph-route visual proof must be nonblank.",
            "Packaged/native visual QA must be runnable under host policy.",
            "Packaged/native visual QA must capture a real native screenshot.",
            "Native screenshot must pass the nonblank gate.",
            "Durable host-policy unblock handoff evidence must be review-only and preserve authority boundaries while the host-policy blocker remains active.",
            "Workspace temp ACL operator handoff evidence must be review-only and preserve authority boundaries while the workspace temp blocker remains active.",
            "Supplemental native screenshot evidence may support manual review but cannot complete automated packaged visual QA.",
            "No host-policy, signing, installer, startup, approval, Agent Bus, provider, connector, or canonical authority may be expanded by the audit.",
        ],
        "prompt_to_artifact_checklist": checklist,
        "browser_visual_verification": browser_visual,
        "host_policy_unblock_readiness": host_policy,
        "host_policy_handoff_evidence": handoff_evidence,
        "packaged_visual_qa_report_evidence": packaged_visual_qa_report,
        "webview2_diagnostic_report_evidence": webview2_diagnostic_report,
        "webview2_policy_check_report_evidence": webview2_policy_check_report,
        "workspace_temp_acl_diagnostic_report_evidence": workspace_temp_acl_diagnostic_report,
        "pywebview_minimal_repro_report_evidence": pywebview_minimal_repro_report,
        "webview2_runtime_host_remediation_report_evidence": webview2_runtime_host_remediation_report,
        "webview2_runtime_remediation_evidence_report_evidence": webview2_runtime_remediation_evidence_report,
        "workspace_temp_acl_operator_handoff_evidence": workspace_temp_handoff_evidence,
        "native_probe_config": {
            "probe_native_host_policy": bool(probe_native_host_policy),
            "settle_seconds": float(native_probe_settle_seconds),
            "window_timeout_seconds": float(native_probe_window_timeout_seconds),
            "terminate_timeout_seconds": float(native_probe_terminate_timeout_seconds),
            "host_policy_probe_executable_source": host_policy_probe_executable_source,
            "host_policy_probe_executable_path": host_policy_probe_executable_path,
        },
        "supplemental_native_screenshot_evidence": supplemental_native_evidence,
        "saved_native_screenshot_evidence_report": saved_native_evidence_report,
        "missing_or_blocked": missing,
        "current_status": status,
        "next_recommended_pass": next_pass,
    }


def format_pass10b_visual_proof_completion_audit(report: dict[str, Any]) -> str:
    lines = [
        f"Pass 10B visual-proof completion audit: {report.get('status')}",
        f"  ok: {report.get('ok')}",
        f"  next: {report.get('next_recommended_pass')}",
    ]
    for item in report.get("prompt_to_artifact_checklist") or []:
        marker = "ok" if item.get("ok") else "missing"
        lines.append(f"  - {item.get('id')}: {marker} ({item.get('status')})")
    return "\n".join(lines)


def write_pass10b_visual_proof_completion_audit_report(
    vault_root: str | Path,
    report: dict[str, Any],
    *,
    report_slug: str | None = None,
    report_root: str | Path | None = None,
) -> dict[str, Any]:
    """Write durable completion-audit evidence inside the vault workspace."""

    vault = _vault_path(vault_root)
    root = Path(report_root) if report_root else DEFAULT_REPORT_ROOT
    if not root.is_absolute():
        root = vault / root
    root = root.resolve()
    try:
        root.relative_to(vault)
    except ValueError as exc:
        raise ValueError("Pass 10B completion audit report root must stay inside the vault workspace") from exc
    slug = report_slug or f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}-pass10b-visual-proof-completion-audit"
    json_path = (root / f"{slug}.json").resolve()
    markdown_path = (root / f"{slug}.md").resolve()
    for path in (json_path, markdown_path):
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise ValueError("Pass 10B completion audit report output must stay inside the report root") from exc
    root.mkdir(parents=True, exist_ok=True)

    payload = {
        "report_type": "pass10b_visual_proof_completion_audit",
        "generated_at": _now_utc(),
        "status": report.get("status"),
        "ok": report.get("ok"),
        "objective": report.get("objective"),
        "success_criteria": report.get("success_criteria"),
        "prompt_to_artifact_checklist": report.get("prompt_to_artifact_checklist"),
        "browser_visual_verification": report.get("browser_visual_verification"),
        "host_policy_handoff_evidence": report.get("host_policy_handoff_evidence"),
        "packaged_visual_qa_report_evidence": report.get("packaged_visual_qa_report_evidence"),
        "webview2_diagnostic_report_evidence": report.get("webview2_diagnostic_report_evidence"),
        "webview2_policy_check_report_evidence": report.get("webview2_policy_check_report_evidence"),
        "workspace_temp_acl_diagnostic_report_evidence": report.get("workspace_temp_acl_diagnostic_report_evidence"),
        "pywebview_minimal_repro_report_evidence": report.get("pywebview_minimal_repro_report_evidence"),
        "webview2_runtime_host_remediation_report_evidence": report.get(
            "webview2_runtime_host_remediation_report_evidence"
        ),
        "webview2_runtime_remediation_evidence_report_evidence": report.get(
            "webview2_runtime_remediation_evidence_report_evidence"
        ),
        "workspace_temp_acl_operator_handoff_evidence": report.get("workspace_temp_acl_operator_handoff_evidence"),
        "native_probe_config": report.get("native_probe_config"),
        "saved_native_screenshot_evidence_report": report.get("saved_native_screenshot_evidence_report"),
        "missing_or_blocked": report.get("missing_or_blocked"),
        "next_recommended_pass": report.get("next_recommended_pass"),
        "authority_note": (
            "This report is evidence-only. It does not mutate host policy, sign or allowlist the executable, "
            "write installer/startup state, execute approvals, write Agent Bus tasks, call providers/connectors, "
            "persist graph state, or mutate canonical state."
        ),
    }
    json_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

    checklist = report.get("prompt_to_artifact_checklist") or []
    blocked = report.get("missing_or_blocked") or []
    lines = [
        "# Pass 10B Visual Proof Completion Audit Report",
        "",
        f"Generated: {payload['generated_at']}",
        "Runtime: Codex",
        f"Status: {report.get('status')}",
        f"OK: {report.get('ok')}",
        f"Next recommended pass: {report.get('next_recommended_pass')}",
        "",
        "## Checklist",
        "",
    ]
    for item in checklist:
        marker = "OK" if item.get("ok") else "BLOCKED"
        lines.append(f"- {item.get('id')}: {marker} / {item.get('status')} - {item.get('evidence')}")
    lines.extend(["", "## Missing Or Blocked", ""])
    if blocked:
        for item in blocked:
            lines.append(f"- {item.get('id')}: {item.get('status')} - {item.get('evidence')}")
    else:
        lines.append("- None")
    handoff = report.get("host_policy_handoff_evidence") or {}
    visual_qa_report = report.get("packaged_visual_qa_report_evidence") or {}
    webview2_report = report.get("webview2_diagnostic_report_evidence") or {}
    webview2_policy_report = report.get("webview2_policy_check_report_evidence") or {}
    workspace_temp_report = report.get("workspace_temp_acl_diagnostic_report_evidence") or {}
    pywebview_minimal_report = report.get("pywebview_minimal_repro_report_evidence") or {}
    webview2_remediation_report = report.get("webview2_runtime_host_remediation_report_evidence") or {}
    webview2_remediation_evidence = report.get("webview2_runtime_remediation_evidence_report_evidence") or {}
    workspace_temp_handoff = report.get("workspace_temp_acl_operator_handoff_evidence") or {}
    lines.extend(
        [
            "",
            "## Handoff Evidence",
            "",
            f"- Path: {handoff.get('path')}",
            f"- Status: {handoff.get('status')}",
            f"- Review-only boundary: {handoff.get('review_only_boundary')}",
            "",
            "## Packaged Visual QA Report Evidence",
            "",
            f"- Path: {visual_qa_report.get('path')}",
            f"- Status: {visual_qa_report.get('status')}",
            f"- Host policy allows launch: {visual_qa_report.get('host_policy_allows_launch')}",
            f"- Native visual QA complete: {visual_qa_report.get('native_visual_qa_complete')}",
            f"- Authority boundary present: {visual_qa_report.get('authority_boundary_present')}",
            "",
            "## WebView2 Diagnostic Evidence",
            "",
            f"- Path: {webview2_report.get('path')}",
            f"- Status: {webview2_report.get('report_status')}",
            f"- Next recommended pass: {webview2_report.get('next_recommended_pass')}",
            "",
            "## WebView2 Temp/Policy Check Evidence",
            "",
            f"- Path: {webview2_policy_report.get('path')}",
            f"- Status: {webview2_policy_report.get('report_status')}",
            f"- Next recommended pass: {webview2_policy_report.get('next_recommended_pass')}",
            "",
            "## Workspace Temp ACL Cleanup Diagnostic Evidence",
            "",
            f"- Path: {workspace_temp_report.get('path')}",
            f"- Status: {workspace_temp_report.get('report_status')}",
            f"- Next recommended pass: {workspace_temp_report.get('next_recommended_pass')}",
            "",
            "## PyWebView WebView2 Minimal Repro Evidence",
            "",
            f"- Path: {pywebview_minimal_report.get('path')}",
            f"- Status: {pywebview_minimal_report.get('report_status')}",
            f"- Source runtime: {pywebview_minimal_report.get('source_runtime_error_status')}",
            f"- Packaged runtime: {pywebview_minimal_report.get('packaged_runtime_error_status')}",
            f"- Next recommended pass: {pywebview_minimal_report.get('next_recommended_pass')}",
            "",
            "## WebView2 Runtime Host Remediation Evidence",
            "",
            f"- Path: {webview2_remediation_report.get('path')}",
            f"- Status: {webview2_remediation_report.get('report_status')}",
            f"- Source runtime: {webview2_remediation_report.get('source_runtime_error_status')}",
            f"- Packaged runtime: {webview2_remediation_report.get('packaged_runtime_error_status')}",
            f"- Authority boundary present: {webview2_remediation_report.get('authority_boundary_present')}",
            f"- Next recommended pass: {webview2_remediation_report.get('next_recommended_pass')}",
            "",
            "## WebView2 Runtime Remediation Evidence Intake",
            "",
            f"- Path: {webview2_remediation_evidence.get('path')}",
            f"- Status: {webview2_remediation_evidence.get('report_status')}",
            f"- Remediation status: {webview2_remediation_evidence.get('remediation_status')}",
            f"- Operator evidence supplied: {webview2_remediation_evidence.get('operator_remediation_evidence_supplied')}",
            f"- Remediation effect verified: {webview2_remediation_evidence.get('remediation_effect_verified')}",
            f"- Authority boundary present: {webview2_remediation_evidence.get('authority_boundary_present')}",
            f"- Next recommended pass: {webview2_remediation_evidence.get('next_recommended_pass')}",
            "",
            "## Workspace Temp ACL Operator Handoff Evidence",
            "",
            f"- Path: {workspace_temp_handoff.get('path')}",
            f"- Status: {workspace_temp_handoff.get('status')}",
            f"- Review-only boundary: {workspace_temp_handoff.get('review_only_boundary')}",
            f"- Next recommended pass: {workspace_temp_handoff.get('next_recommended_pass')}",
            "",
            "## Authority Boundary",
            "",
            f"- {payload['authority_note']}",
        ]
    )
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return {
        "written": True,
        "json_path": _relative(vault, json_path),
        "markdown_path": _relative(vault, markdown_path),
    }
