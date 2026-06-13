"""Read-only Phase 10 Studio product hardening status.

This contract composes the current native shell, packaging, installer, and
Browser Runtime closeout state. It performs no launches, builds, installer
writes, approval decisions, provider calls, connector calls, or canonical
mutation.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.browser_runtime.production_closeout import build_browser_runtime_production_closeout
from runtime.studio.installer_plan import build_studio_installer_plan
from runtime.studio.packaging_readiness import build_studio_packaging_readiness
from runtime.studio.shell.panel_registry import build_native_shell_panel_registry


MODEL_VERSION = "studio.product_hardening_status.v1"
SURFACE_ID = "studio_product_hardening_status"
DEFAULT_EVIDENCE_ROOT = Path("07_LOGS") / "Studio-Graph-Views"
NEXT_PRODUCT_HARDENING_PASS = "phase10-studio-product-hardening"
NEXT_RELEASE_GOVERNANCE_PASS = "studio-release-readiness-governance"
MIN_EXPECTED_MOUNTED_PANEL_COUNT = 13

BLOCKED_AUTHORITY = {
    "read_only": True,
    "local_only": True,
    "launches_pywebview": False,
    "starts_servers": False,
    "builds_executable": False,
    "launches_executable": False,
    "writes_installer": False,
    "signs_artifacts": False,
    "writes_host_startup": False,
    "registers_autostart": False,
    "writes_registry": False,
    "writes_start_menu": False,
    "writes_desktop_shortcut": False,
    "browser_use_cli_live_run": False,
    "excalidraw_live_proof": False,
    "approval_grant": False,
    "approval_execution": False,
    "mutates_gate": False,
    "executes_workflows": False,
    "provider_calls_allowed": False,
    "connector_calls_allowed": False,
    "writes_agent_bus_tasks": False,
    "canonical_mutation_allowed": False,
}


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _relative_to_vault(vault: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(vault.resolve()).as_posix()
    except ValueError:
        return str(path)


def _file_record(vault: Path, relative_path: str) -> dict[str, Any]:
    path = vault / relative_path
    return {
        "path": relative_path,
        "exists": path.is_file(),
        "size_bytes": path.stat().st_size if path.is_file() else 0,
    }


def _glob_records(vault: Path, pattern: str) -> list[dict[str, Any]]:
    root = vault / DEFAULT_EVIDENCE_ROOT
    return [
        {
            "path": _relative_to_vault(vault, path),
            "exists": path.is_file(),
            "size_bytes": path.stat().st_size if path.is_file() else 0,
        }
        for path in sorted(root.glob(pattern))
        if path.is_file()
    ]


def _all_false(payload: dict[str, Any], keys: list[str]) -> bool:
    return not any(bool(payload.get(key)) for key in keys)


def _browser_runtime_closeout(vault: Path, generated_at: str) -> tuple[dict[str, Any] | None, str | None]:
    try:
        return build_browser_runtime_production_closeout(vault, generated_at=generated_at).to_dict(), None
    except ValueError as exc:
        return None, str(exc)


def build_studio_product_hardening_status(
    vault_root: str | Path,
    *,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Return the current Phase 10 product-hardening status without side effects."""

    vault = _vault_path(vault_root)
    timestamp = generated_at or _now_utc()
    panel_registry = build_native_shell_panel_registry(vault)
    packaging_readiness = build_studio_packaging_readiness(vault)
    installer_plan = build_studio_installer_plan(vault)
    closeout, closeout_error = _browser_runtime_closeout(vault, timestamp)
    panel_readiness = panel_registry.get("readiness") or {}
    installer_prerequisites = installer_plan.get("prerequisites") or {}
    installer_evidence = installer_plan.get("evidence") or {}
    pass10b_audit_evidence = installer_evidence.get("pass10b_completion_audit") or {}
    authority_false_keys = [key for key, value in BLOCKED_AUTHORITY.items() if value is False]

    production_complete_evidence = _glob_records(vault, "*browser-runtime-production-complete.json")
    installer_plan_md_evidence = _glob_records(vault, "*studio-installer-plan*.md")
    required_evidence = {
        "browser_runtime_production_complete_json": bool(production_complete_evidence),
        "studio_local_packaging_proof_md": bool((installer_evidence.get("local_packaging_proof") or {}).get("exists")),
        "packaged_app_launch_smoke_json": bool((installer_evidence.get("launch_smoke_json") or {}).get("exists")),
        "packaged_app_visual_qa_json": bool((installer_evidence.get("visual_qa_json") or {}).get("exists")),
        "packaged_app_visual_qa_png": bool((installer_evidence.get("visual_qa_png") or {}).get("exists")),
        "pass10b_completion_audit_json": bool(
            pass10b_audit_evidence.get("exists")
            and pass10b_audit_evidence.get("report_type_valid")
        ),
        "installer_plan_md": bool(installer_plan_md_evidence),
    }
    browser_runtime_complete = bool(
        closeout
        and closeout.get("status") == "browser_runtime_production_complete"
        and closeout.get("production_feature_done") is True
        and closeout.get("remaining_major_passes_min") == 0
        and closeout.get("remaining_major_passes_max") == 0
    )
    panel_registry_ready = bool(
        panel_registry.get("surface") == "studio_native_shell_panel_registry"
        and panel_readiness.get("native_shell_primary") is True
        and panel_readiness.get("native_shell_panel_registry_ready") is True
        and panel_readiness.get("mounted_panel_count", 0) >= MIN_EXPECTED_MOUNTED_PANEL_COUNT
        and panel_readiness.get("all_declared_panels_safe_or_approval_gated") is True
        and panel_readiness.get("direct_write_authority_blocked") is True
        and panel_readiness.get("blocked_authority_exposed") is True
    )
    installer_governance_ready = bool(
        installer_plan.get("ok")
        and installer_plan.get("status") == "ready_for_governed_installer_design"
        and installer_prerequisites.get("visual_qa_evidence_present") is True
        and installer_prerequisites.get("visual_qa_ok") is True
        and _all_false(installer_plan.get("authority") or {}, list((installer_plan.get("authority") or {}).keys()))
    )
    packaging_readiness_ready = bool(packaging_readiness.get("ok"))
    no_mutation_authority = _all_false(BLOCKED_AUTHORITY, authority_false_keys)
    blockers: list[str] = []
    if not panel_registry_ready:
        blockers.append("Native shell panel registry is not fully ready or approval-gated safe.")
    if closeout_error:
        blockers.append(f"Browser Runtime production closeout could not be composed: {closeout_error}")
    elif not browser_runtime_complete:
        blockers.append("Browser Runtime production closeout is not complete.")
    if not packaging_readiness_ready:
        blockers.append("Studio packaging readiness contract is not green.")
    if not installer_governance_ready:
        blockers.append("Installer governance plan is not ready or lacks required visual QA evidence.")
    missing_evidence = [key for key, exists in required_evidence.items() if not exists]
    if missing_evidence:
        blockers.append(f"Required Phase 10 evidence is missing: {', '.join(missing_evidence)}.")
    if not no_mutation_authority:
        blockers.append("Product hardening status exposes mutation authority.")

    ok = not blockers
    return {
        "ok": ok,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "status": "studio_product_hardened_ready_for_release_governance" if ok else "blocked_product_hardening",
        "generated_at": timestamp,
        "vault_root": str(vault),
        "product_lane": {
            "primary": "native_pywebview_shell",
            "primary_command": "chaseos studio shell",
            "legacy_localhost_harness_secondary": True,
            "legacy_harness_command": "chaseos studio desktop-shell-app",
        },
        "summary": {
            "native_shell_primary": bool(panel_readiness.get("native_shell_primary")),
            "declared_panel_count": panel_readiness.get("declared_panel_count"),
            "mounted_panel_count": panel_readiness.get("mounted_panel_count"),
            "approval_gated_panel_count": panel_readiness.get("approval_gated_panel_count"),
            "browser_runtime_production_complete": browser_runtime_complete,
            "packaging_readiness_ready": packaging_readiness_ready,
            "installer_governance_ready": installer_governance_ready,
            "release_governance_deferred": True,
        },
        "readiness": {
            "product_hardening_status_ready": ok,
            "panel_registry_ready": panel_registry_ready,
            "browser_runtime_production_complete": browser_runtime_complete,
            "packaging_readiness_ready": packaging_readiness_ready,
            "installer_governance_ready": installer_governance_ready,
            "required_evidence_present": all(required_evidence.values()),
            "no_mutation_authority": no_mutation_authority,
            "next_recommended_pass": NEXT_RELEASE_GOVERNANCE_PASS if ok else NEXT_PRODUCT_HARDENING_PASS,
        },
        "evidence": {
            "browser_runtime_production_complete": production_complete_evidence,
            "required_evidence": required_evidence,
            "installer_plan": installer_plan.get("evidence"),
            "packaged_app": installer_plan.get("packaged_app"),
        },
        "source_contracts": {
            "panel_registry": {
                "ok": panel_registry.get("surface") == "studio_native_shell_panel_registry",
                "status": "ready" if panel_registry_ready else "blocked",
                "next_recommended_pass": panel_readiness.get("next_recommended_pass"),
            },
            "packaging_readiness": {
                "ok": packaging_readiness_ready,
                "status": packaging_readiness.get("status"),
                "next_recommended_pass": packaging_readiness.get("next_recommended_pass"),
            },
            "installer_plan": {
                "ok": bool(installer_plan.get("ok")),
                "status": installer_plan.get("status"),
                "next_recommended_pass": installer_plan.get("next_recommended_pass"),
            },
            "browser_runtime_production_closeout": {
                "ok": browser_runtime_complete,
                "status": (closeout or {}).get("status") if closeout else "blocked",
                "next_recommended_pass": (closeout or {}).get("next_recommended_pass"),
                "error": closeout_error,
            },
        },
        "deferred_governed_items": [
            {
                "id": "governed-installer-build-approval",
                "status": "deferred_governed",
                "required_before": ["writes_installer"],
            },
            {
                "id": "signing-approval",
                "status": "deferred_governed",
                "required_before": ["signs_artifacts"],
            },
            {
                "id": "startup-autostart-approval",
                "status": "deferred_governed",
                "required_before": ["writes_host_startup", "registers_autostart", "writes_registry"],
            },
            {
                "id": "release-promotion-approval",
                "status": "deferred_governed",
                "required_before": ["canonical_release_status", "public_release"],
            },
        ],
        "authority": dict(BLOCKED_AUTHORITY),
        "blocked_authority": [key for key, value in BLOCKED_AUTHORITY.items() if value is False],
        "blockers": blockers,
        "unverified": [
            "No native PyWebView window was launched by this status contract.",
            "No packaged app was launched by this status contract.",
            "No installer was created or signed by this status contract.",
            "No startup/autostart integration was attempted.",
            "No approval decision, Gate mutation, provider/connector call, Agent Bus task write, Browser Use CLI live run, Excalidraw live proof, or canonical writeback was performed.",
        ],
        "next_recommended_pass": NEXT_RELEASE_GOVERNANCE_PASS if ok else NEXT_PRODUCT_HARDENING_PASS,
    }
