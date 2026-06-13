"""Read-only installer/signing/startup governance plan for ChaseOS Studio."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from runtime.studio.packaged_app_launch_smoke import DEFAULT_EXE, _relative_to_vault, _resolve_executable
from runtime.studio.packaging_proof import build_studio_local_packaging_proof, _sha256
from runtime.studio.packaging_readiness import build_studio_packaging_readiness


MODEL_VERSION = "studio.installer_plan.v1"
SURFACE_ID = "studio_installer_plan"
DEFAULT_EVIDENCE_ROOT = Path("07_LOGS") / "Studio-Graph-Views"
VISUAL_QA_EVIDENCE_ROOT = Path("07_LOGS") / "Visual-QA"
PASS10B_COMPLETION_AUDIT_ROOT = DEFAULT_EVIDENCE_ROOT / "pass10b-completion-audits"
VISUAL_QA_SLUG = "2026-05-04-studio-packaged-app-visual-qa"
LAUNCH_SMOKE_SLUG = "2026-05-04-studio-packaged-app-launch-smoke"
LOCAL_PACKAGING_SLUG = "2026-05-04-studio-local-packaging-proof"

BLOCKED_AUTHORITY = {
    "builds_executable": False,
    "writes_installer": False,
    "signs_artifacts": False,
    "writes_host_startup": False,
    "registers_autostart": False,
    "writes_registry": False,
    "writes_start_menu": False,
    "writes_desktop_shortcut": False,
    "mutates_gate": False,
    "grants_approvals": False,
    "executes_approval_decisions": False,
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


def _evidence_file(vault: Path, slug: str, suffix: str) -> Path:
    return vault / DEFAULT_EVIDENCE_ROOT / f"{slug}.{suffix}"


def _file_record(vault: Path, path: Path) -> dict[str, Any]:
    return {
        "path": _relative_to_vault(vault, path),
        "exists": path.is_file(),
        "size_bytes": path.stat().st_size if path.is_file() else 0,
    }


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _payload(path: Path) -> dict[str, Any]:
    data = _load_json(path)
    return data.get("result") or data


def _timestamp_from_payload(payload: dict[str, Any]) -> float:
    generated_at = payload.get("generated_at")
    if isinstance(generated_at, str) and generated_at:
        try:
            return datetime.fromisoformat(generated_at.replace("Z", "+00:00")).timestamp()
        except ValueError:
            return 0.0
    return 0.0


def _latest_surface_report(vault: Path, surface: str) -> Path | None:
    candidates: list[Path] = []
    for root, recursive in (
        (vault / DEFAULT_EVIDENCE_ROOT, False),
        (vault / VISUAL_QA_EVIDENCE_ROOT, True),
    ):
        if not root.is_dir():
            continue
        try:
            paths = root.rglob("*.json") if recursive else root.glob("*.json")
            for path in paths:
                if not path.is_file():
                    continue
                payload = _payload(path)
                if payload.get("surface") == surface:
                    candidates.append(path)
        except OSError:
            continue
    if not candidates:
        return None
    return max(candidates, key=lambda path: (_timestamp_from_payload(_payload(path)), path.stat().st_mtime))


def _latest_or_legacy_surface_report(vault: Path, surface: str, legacy_slug: str) -> Path:
    return _latest_surface_report(vault, surface) or _evidence_file(vault, legacy_slug, "json")


def _related_markdown_path(json_path: Path) -> Path:
    return json_path.with_suffix(".md")


def _path_from_report_value(vault: Path, value: str | None) -> Path | None:
    if not value:
        return None
    path = Path(value)
    if not path.is_absolute():
        path = vault / path
    return path.resolve()


def _visual_screenshot_path(vault: Path, visual_report: dict[str, Any], fallback_slug: str) -> Path:
    evidence = visual_report.get("evidence") or {}
    screenshot = visual_report.get("screenshot") or {}
    for value in (evidence.get("screenshot_path"), screenshot.get("path")):
        path = _path_from_report_value(vault, value)
        if path is not None:
            return path
    return _evidence_file(vault, fallback_slug, "png")


def _latest_packaged_executable(vault: Path) -> Path | None:
    report_path = _latest_surface_report(vault, "studio_local_packaging_proof")
    if report_path is None:
        return None
    outputs = _payload(report_path).get("outputs") or {}
    path = _path_from_report_value(vault, outputs.get("expected_executable"))
    if path is None or not path.is_file():
        return None
    try:
        path.relative_to(vault)
    except ValueError:
        return None
    return path


def _latest_pass10b_completion_audit(vault: Path) -> Path | None:
    root = vault / PASS10B_COMPLETION_AUDIT_ROOT
    if not root.is_dir():
        return None
    candidates = [path for path in root.glob("*.json") if path.is_file()]
    if not candidates:
        return None
    complete_candidates = [path for path in candidates if _audit_payload_is_complete(_payload(path))]
    if complete_candidates:
        return max(complete_candidates, key=_audit_recency_key)
    return max(candidates, key=_audit_recency_key)


def _audit_recency_key(path: Path) -> tuple[float, float]:
    payload = _payload(path)
    generated_at = payload.get("generated_at")
    generated_timestamp = 0.0
    if isinstance(generated_at, str) and generated_at:
        try:
            generated_timestamp = datetime.fromisoformat(generated_at.replace("Z", "+00:00")).timestamp()
        except ValueError:
            generated_timestamp = 0.0
    return (generated_timestamp, path.stat().st_mtime)


def _audit_payload_is_complete(payload: dict[str, Any]) -> bool:
    payload = payload.get("result") or payload
    return (
        payload.get("report_type") == "pass10b_visual_proof_completion_audit"
        and bool(payload.get("ok"))
        and _checklist_ok(payload, "native_packaged_visual_qa_complete")
        and _checklist_ok(payload, "packaged_visual_qa_saved_report_valid")
    )


def _checklist_ok(payload: dict[str, Any], item_id: str) -> bool:
    for item in payload.get("prompt_to_artifact_checklist") or []:
        if item.get("id") == item_id:
            return item.get("ok") is True
    return False


def _checklist_missing_or_blocked_ids(payload: dict[str, Any]) -> list[str]:
    return [
        str(item.get("id"))
        for item in payload.get("prompt_to_artifact_checklist") or []
        if item.get("id") and item.get("ok") is not True
    ]


def _inspect_pass10b_completion_audit(vault: Path) -> dict[str, Any]:
    path = _latest_pass10b_completion_audit(vault)
    if path is None:
        return {
            "path": None,
            "exists": False,
            "status": None,
            "ok": False,
            "report_type_valid": False,
            "native_host_policy_allows_launch": False,
            "native_packaged_visual_qa_complete": False,
            "packaged_visual_qa_saved_report_valid": False,
            "blocks_installer_visual_qa": False,
            "missing_or_blocked_ids": [],
        }

    payload = _load_json(path)
    payload = payload.get("result") or payload
    report_type_valid = payload.get("report_type") == "pass10b_visual_proof_completion_audit"
    native_visual_qa_complete = _checklist_ok(payload, "native_packaged_visual_qa_complete")
    ok = bool(payload.get("ok")) and native_visual_qa_complete
    return {
        "path": _relative_to_vault(vault, path),
        "exists": True,
        "status": payload.get("status"),
        "ok": ok,
        "report_type_valid": report_type_valid,
        "native_host_policy_allows_launch": _checklist_ok(payload, "native_host_policy_allows_launch"),
        "native_packaged_visual_qa_complete": native_visual_qa_complete,
        "packaged_visual_qa_saved_report_valid": _checklist_ok(payload, "packaged_visual_qa_saved_report_valid"),
        "blocks_installer_visual_qa": report_type_valid and not ok,
        "missing_or_blocked_ids": _checklist_missing_or_blocked_ids(payload),
    }


def build_studio_installer_plan(
    vault_root: str | Path,
    *,
    executable_path: str | Path | None = None,
) -> dict[str, Any]:
    """Build a read-only installer governance plan without creating an installer."""

    vault = _vault_path(vault_root)
    exe = _resolve_executable(vault, executable_path or DEFAULT_EXE)
    if executable_path is None and not exe.is_file():
        latest_exe = _latest_packaged_executable(vault)
        if latest_exe is not None:
            exe = latest_exe
    readiness = build_studio_packaging_readiness(vault)
    packaging_proof = build_studio_local_packaging_proof(vault)
    launch_json = _latest_or_legacy_surface_report(vault, "studio_packaged_app_launch_smoke", LAUNCH_SMOKE_SLUG)
    visual_json = _latest_or_legacy_surface_report(vault, "studio_packaged_app_visual_qa", VISUAL_QA_SLUG)
    packaging_json = _latest_or_legacy_surface_report(vault, "studio_local_packaging_proof", LOCAL_PACKAGING_SLUG)
    visual_report = _payload(visual_json)
    launch_report = _payload(launch_json)
    packaging_report = _payload(packaging_json)
    visual_png = _visual_screenshot_path(vault, visual_report, VISUAL_QA_SLUG)
    packaging_md = _related_markdown_path(packaging_json)
    pass10b_audit = _inspect_pass10b_completion_audit(vault)
    pass10b_gate_applies = pass10b_audit["exists"] and pass10b_audit["report_type_valid"]
    legacy_visual_qa_ok = bool(visual_report.get("ok")) if visual_report else False
    packaging_proof_ok = bool(packaging_proof.get("ok")) or bool(packaging_report.get("ok"))
    packaged_executable_sha256 = (
        _sha256(exe)
        or (packaging_proof.get("outputs") or {}).get("executable_sha256")
        or ((packaging_report.get("outputs") or {}).get("executable_sha256"))
    )
    visual_qa_ok = legacy_visual_qa_ok and (
        not pass10b_gate_applies
        or (
            pass10b_audit["ok"] is True
            and pass10b_audit["native_packaged_visual_qa_complete"] is True
        )
    )

    prerequisites = {
        "packaging_readiness_ok": bool(readiness.get("ok")),
        "local_packaging_proof_ok": packaging_proof_ok,
        "packaged_executable_exists": exe.is_file(),
        "packaged_executable_sha256": packaged_executable_sha256,
        "launch_smoke_evidence_present": launch_json.is_file(),
        "launch_smoke_ok": bool(launch_report.get("ok")) if launch_report else False,
        "visual_qa_evidence_present": visual_json.is_file() and visual_png.is_file(),
        "latest_visual_qa_ok": legacy_visual_qa_ok,
        "legacy_visual_qa_ok": legacy_visual_qa_ok,
        "pass10b_completion_audit_present": pass10b_audit["exists"],
        "pass10b_completion_audit_ok": pass10b_audit["ok"] if pass10b_gate_applies else None,
        "pass10b_native_visual_qa_complete": (
            pass10b_audit["native_packaged_visual_qa_complete"] if pass10b_gate_applies else None
        ),
        "visual_qa_ok": visual_qa_ok,
    }
    blockers: list[str] = []
    if not prerequisites["packaging_readiness_ok"]:
        blockers.append("Packaging readiness is not green.")
    if not prerequisites["local_packaging_proof_ok"]:
        packaging_blockers = packaging_proof.get("blockers") or []
        detail = f": {'; '.join(str(item) for item in packaging_blockers)}" if packaging_blockers else "."
        blockers.append(f"Local packaging proof is not green{detail}")
    if not prerequisites["packaged_executable_exists"]:
        blockers.append("Packaged Studio executable is missing.")
    if not prerequisites["launch_smoke_evidence_present"]:
        blockers.append("Packaged app launch smoke evidence is missing.")
    if not prerequisites["visual_qa_evidence_present"]:
        blockers.append("Packaged app visual QA evidence is missing.")
    if visual_report and not legacy_visual_qa_ok:
        blockers.append("Latest packaged app visual QA is not green.")
    if pass10b_gate_applies and not pass10b_audit["native_packaged_visual_qa_complete"]:
        blockers.append("Latest Pass 10B completion audit does not verify native packaged visual QA.")
    elif pass10b_gate_applies and not pass10b_audit["ok"]:
        blockers.append("Latest Pass 10B completion audit is not green.")

    ok = not blockers
    return {
        "ok": ok,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "status": "ready_for_governed_installer_design" if ok else "blocked_installer_plan",
        "generated_at": _now_utc(),
        "vault_root": str(vault),
        "product_lane": {
            "primary": "native_pywebview_shell",
            "primary_command": "chaseos studio shell",
            "legacy_localhost_harness_secondary": True,
        },
        "packaged_app": {
            "executable": _file_record(vault, exe),
            "sha256": prerequisites["packaged_executable_sha256"],
            "visual_qa_screenshot": _file_record(vault, visual_png),
        },
        "prerequisites": prerequisites,
        "evidence": {
            "local_packaging_proof": _file_record(vault, packaging_md),
            "launch_smoke_json": _file_record(vault, launch_json),
            "visual_qa_json": _file_record(vault, visual_json),
            "visual_qa_png": _file_record(vault, visual_png),
            "pass10b_completion_audit": pass10b_audit,
        },
        "installer_plan": {
            "target_platforms": [
                {
                    "id": "windows",
                    "status": "planned",
                    "candidate_formats": ["zip-portable", "msix", "msi-or-inno-setup"],
                    "recommended_first_proof": "zip-portable",
                    "reason": "Portable ZIP proof can validate packaged app layout without registry/startup writes.",
                }
            ],
            "artifact_boundaries": [
                "Installer output must live under a declared packaging output root until explicitly promoted.",
                "Installer build must not read secrets or credential files.",
                "Installer metadata must describe localhost harness as test support, not product shell truth.",
                "Native PyWebView shell assets must be bundled from the local package-data/MEIPASS path.",
            ],
            "future_write_roots": [
                ".pytest_tmp_env/studio-installer-proof/",
                "dist/ChaseOS-Studio/",
            ],
        },
        "governance_gates": [
            {
                "id": "installer-build-approval",
                "status": "required_before_write",
                "required_before": ["writes_installer", "writes_packaging_output_root"],
                "proof_required": ["dry_run_plan", "expected_output_paths", "owned_process_cleanup"],
            },
            {
                "id": "signing-approval",
                "status": "required_before_write",
                "required_before": ["signs_artifacts", "certificate_access"],
                "proof_required": ["certificate_source_policy", "no_secret_value_display", "audit_record"],
            },
            {
                "id": "startup-autostart-approval",
                "status": "required_before_host_mutation",
                "required_before": ["writes_host_startup", "registers_autostart", "writes_registry"],
                "proof_required": ["dry_run", "rollback_plan", "exact_once_marker", "operator_confirmation"],
            },
            {
                "id": "release-promotion-approval",
                "status": "required_before_release",
                "required_before": ["public_release", "canonical_release_status"],
                "proof_required": ["visual_qa", "launch_smoke", "installer_hash", "governance_audit"],
            },
        ],
        "runtime_boundaries": {
            "desktop_shell_app_role": "compatibility_test_harness",
            "desktop_shell_app_is_product_shell": False,
            "native_shell_is_product_shell": True,
            "installer_must_not_bypass_gate": True,
            "installer_must_not_bypass_runtime_startup_controls": True,
            "installer_must_not_execute_workflows": True,
            "installer_must_not_grant_approvals": True,
        },
        "authority": BLOCKED_AUTHORITY,
        "blocked_authority": [key for key, value in BLOCKED_AUTHORITY.items() if value is False],
        "blockers": blockers,
        "unverified": [
            "No installer was created.",
            "No installer signing was attempted.",
            "No host startup/autostart integration was attempted.",
            "No rollback/audit proof for future startup mutation has been implemented.",
        ],
        "next_recommended_pass": "studio-governed-installer-build-approval" if ok else "studio-installer-plan-and-governance",
    }


def write_installer_plan_evidence(
    vault_root: str | Path,
    report: dict[str, Any],
    *,
    evidence_slug: str | None = None,
    evidence_root: str | Path | None = None,
) -> dict[str, Any]:
    vault = _vault_path(vault_root)
    root = vault / (Path(evidence_root) if evidence_root else DEFAULT_EVIDENCE_ROOT)
    root.mkdir(parents=True, exist_ok=True)
    slug = evidence_slug or f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}-studio-installer-plan-and-governance"
    json_path = root / f"{slug}.json"
    markdown_path = root / f"{slug}.md"
    json_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    lines = [
        "# Studio Installer Plan and Governance Evidence",
        "",
        f"Generated: {report.get('generated_at')}",
        "Runtime: Codex",
        f"Status: {report.get('status')}",
        f"OK: {report.get('ok')}",
        "",
        "## Prerequisites",
        "",
        *[f"- {key}: {value}" for key, value in (report.get("prerequisites") or {}).items()],
        "",
        "## Governance Gates",
        "",
        *[
            f"- {gate.get('id')}: {gate.get('status')} before {', '.join(gate.get('required_before') or [])}"
            for gate in report.get("governance_gates") or []
        ],
        "",
        "## Authority",
        "",
        *[f"- {key}: {value}" for key, value in (report.get("authority") or {}).items()],
        "",
        "## Unverified",
        "",
        *[f"- {item}" for item in report.get("unverified") or []],
    ]
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "written": True,
        "json_path": _relative_to_vault(vault, json_path),
        "markdown_path": _relative_to_vault(vault, markdown_path),
    }
