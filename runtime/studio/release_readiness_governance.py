"""Read-only release-readiness governance gate for ChaseOS Studio.

This contract verifies that Studio can move from product hardening into
operator-reviewed release governance. It does not create approval artifacts,
build installers, sign artifacts, mutate startup/autostart, promote a release,
execute approvals, call providers/connectors, enqueue Agent Bus work, mutate
Gate, or write canonical ChaseOS state.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from runtime.studio.installer_plan import build_studio_installer_plan
from runtime.studio.product_hardening_status import build_studio_product_hardening_status


MODEL_VERSION = "studio.release_readiness_governance.v1"
SURFACE_ID = "studio_release_readiness_governance"
DEFAULT_EVIDENCE_ROOT = Path("07_LOGS") / "Studio-Graph-Views"
NEXT_RELEASE_GOVERNANCE_PASS = "studio-release-readiness-governance"
NEXT_INSTALLER_APPROVAL_PASS = "studio-governed-installer-build-approval"

REQUIRED_GATE_IDS = (
    "installer-build-approval",
    "signing-approval",
    "startup-autostart-approval",
    "release-promotion-approval",
)

BLOCKED_AUTHORITY = {
    "read_only": True,
    "local_only": True,
    "creates_approval_artifact": False,
    "consumes_approval_decision": False,
    "grants_approvals": False,
    "executes_approval_decisions": False,
    "builds_executable": False,
    "writes_installer": False,
    "signs_artifacts": False,
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
    "browser_use_cli_live_run": False,
    "excalidraw_live_proof": False,
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


def _all_false(payload: dict[str, Any], keys: list[str]) -> bool:
    return not any(bool(payload.get(key)) for key in keys)


def _gate_by_id(installer_plan: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(item.get("id")): item
        for item in installer_plan.get("governance_gates") or []
        if item.get("id")
    }


def _approval_requirements(gates: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for gate_id in REQUIRED_GATE_IDS:
        gate = gates.get(gate_id) or {}
        rows.append(
            {
                "id": gate_id,
                "declared": bool(gate),
                "status": gate.get("status") or "missing",
                "required_before": gate.get("required_before") or [],
                "proof_required": gate.get("proof_required") or [],
                "operator_approval_required": True,
                "approval_artifact_present": False,
                "approval_consumed": False,
                "execution_allowed": False,
            }
        )
    return rows


def build_studio_release_readiness_governance(
    vault_root: str | Path,
    *,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Build a no-execution release-readiness governance report."""

    vault = _vault_path(vault_root)
    timestamp = generated_at or _now_utc()
    product = build_studio_product_hardening_status(vault, generated_at=timestamp)
    installer = build_studio_installer_plan(vault)
    gates = _gate_by_id(installer)
    approval_requirements = _approval_requirements(gates)
    authority_false_keys = [key for key, value in BLOCKED_AUTHORITY.items() if value is False]
    product_ok = bool(product.get("ok"))
    installer_ok = bool(installer.get("ok"))
    all_gates_declared = set(REQUIRED_GATE_IDS).issubset(gates)
    no_mutation_authority = _all_false(BLOCKED_AUTHORITY, authority_false_keys) and _all_false(
        installer.get("authority") or {},
        list((installer.get("authority") or {}).keys()),
    )

    blockers: list[str] = []
    if not product_ok:
        blockers.append("Studio product hardening status is not ready.")
    if not installer_ok:
        blockers.append("Studio installer plan is not ready.")
    if not all_gates_declared:
        missing = [gate_id for gate_id in REQUIRED_GATE_IDS if gate_id not in gates]
        blockers.append(f"Required release governance gates are missing: {', '.join(missing)}.")
    if not no_mutation_authority:
        blockers.append("Release-readiness governance exposes mutation authority.")

    ok = not blockers
    return {
        "ok": ok,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "status": "ready_for_operator_release_governance_review" if ok else "blocked_release_readiness_governance",
        "generated_at": timestamp,
        "vault_root": str(vault),
        "product_lane": {
            "primary": "native_pywebview_shell",
            "primary_command": "chaseos studio shell",
            "legacy_localhost_harness_secondary": True,
        },
        "summary": {
            "product_hardening_ready": product_ok,
            "installer_plan_ready": installer_ok,
            "governance_gate_count": len(gates),
            "required_gate_count": len(REQUIRED_GATE_IDS),
            "all_required_gates_declared": all_gates_declared,
            "release_actions_allowed": False,
            "next_recommended_pass": NEXT_INSTALLER_APPROVAL_PASS if ok else NEXT_RELEASE_GOVERNANCE_PASS,
        },
        "readiness": {
            "release_readiness_governance_ready": ok,
            "product_hardening_ready": product_ok,
            "installer_plan_ready": installer_ok,
            "all_governance_gates_declared": all_gates_declared,
            "operator_approval_required_before_release_actions": True,
            "approval_artifacts_required_before_execution": True,
            "dry_run_required_before_write": True,
            "exact_once_marker_required_before_write": True,
            "rollback_audit_required_before_host_mutation": True,
            "no_secret_values_allowed": True,
            "release_actions_allowed": False,
            "no_mutation_authority": no_mutation_authority,
            "next_recommended_pass": NEXT_INSTALLER_APPROVAL_PASS if ok else NEXT_RELEASE_GOVERNANCE_PASS,
        },
        "source_contracts": {
            "product_hardening_status": {
                "ok": product_ok,
                "status": product.get("status"),
                "next_recommended_pass": product.get("next_recommended_pass"),
            },
            "installer_plan": {
                "ok": installer_ok,
                "status": installer.get("status"),
                "next_recommended_pass": installer.get("next_recommended_pass"),
            },
        },
        "approval_requirements": approval_requirements,
        "release_sequence": [
            {
                "step": "installer_build_approval_packet",
                "status": "next_governed_pass" if ok else "blocked",
                "required_gate": "installer-build-approval",
                "writes_allowed_now": False,
            },
            {
                "step": "installer_build_dry_run",
                "status": "deferred",
                "required_before": ["writes_installer"],
                "writes_allowed_now": False,
            },
            {
                "step": "signing_approval",
                "status": "deferred",
                "required_gate": "signing-approval",
                "writes_allowed_now": False,
            },
            {
                "step": "startup_autostart_approval",
                "status": "deferred",
                "required_gate": "startup-autostart-approval",
                "writes_allowed_now": False,
            },
            {
                "step": "release_promotion_approval",
                "status": "deferred",
                "required_gate": "release-promotion-approval",
                "writes_allowed_now": False,
            },
        ],
        "evidence_inputs": {
            "product_hardening": product.get("evidence"),
            "installer_plan": installer.get("evidence"),
            "packaged_app": installer.get("packaged_app"),
        },
        "authority": dict(BLOCKED_AUTHORITY),
        "blocked_authority": [key for key, value in BLOCKED_AUTHORITY.items() if value is False],
        "blockers": blockers,
        "unverified": [
            "No approval artifact was created.",
            "No approval decision was consumed.",
            "No installer build, signing, startup/autostart, release promotion, or canonical release status write was attempted.",
            "No PyWebView launch, server start, packaged executable launch, Browser Use CLI live run, Excalidraw live proof, provider/connector call, Agent Bus task write, Gate mutation, workflow execution, or canonical writeback was performed.",
        ],
        "next_recommended_pass": NEXT_INSTALLER_APPROVAL_PASS if ok else NEXT_RELEASE_GOVERNANCE_PASS,
    }


def write_release_readiness_governance_evidence(
    vault_root: str | Path,
    report: dict[str, Any],
    *,
    evidence_slug: str | None = None,
    evidence_root: str | Path | None = None,
) -> dict[str, Any]:
    vault = _vault_path(vault_root)
    root = vault / (Path(evidence_root) if evidence_root else DEFAULT_EVIDENCE_ROOT)
    root.mkdir(parents=True, exist_ok=True)
    slug = evidence_slug or f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}-studio-release-readiness-governance"
    json_path = root / f"{slug}.json"
    markdown_path = root / f"{slug}.md"
    json_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    lines = [
        "# Studio Release Readiness Governance Evidence",
        "",
        f"Generated: {report.get('generated_at')}",
        "Runtime: Codex",
        f"Status: {report.get('status')}",
        f"OK: {report.get('ok')}",
        f"Next: {report.get('next_recommended_pass')}",
        "",
        "## Summary",
        "",
        *[f"- {key}: {value}" for key, value in (report.get("summary") or {}).items()],
        "",
        "## Approval Requirements",
        "",
        *[
            f"- {item.get('id')}: declared={item.get('declared')} status={item.get('status')} execution_allowed={item.get('execution_allowed')}"
            for item in report.get("approval_requirements") or []
        ],
        "",
        "## Authority",
        "",
        *[f"- {key}: {value}" for key, value in (report.get("authority") or {}).items()],
        "",
        "## Blockers",
        "",
        *[f"- {item}" for item in (report.get("blockers") or ["None"])],
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
