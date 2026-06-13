"""Review-only operator packet for Pass 10B WebView2 remediation."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from runtime.studio.packaged_app_launch_smoke import _relative_to_vault
from runtime.studio.webview2_post_remediation_rerun_readiness import (
    DEFAULT_REPORT_ROOT as POST_REMEDIATION_READINESS_ROOT,
)
from runtime.studio.webview2_runtime_host_remediation import (
    DEFAULT_REPORT_ROOT as HOST_REMEDIATION_ROOT,
)
from runtime.studio.webview2_runtime_remediation_evidence import (
    DEFAULT_REPORT_ROOT as REMEDIATION_EVIDENCE_ROOT,
)


MODEL_VERSION = "studio.webview2_operator_remediation_packet.v1"
SURFACE_ID = "studio_webview2_operator_remediation_packet"
DEFAULT_REPORT_ROOT = Path("07_LOGS") / "Studio-Graph-Views" / "webview2-operator-remediation-packets"


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
        raise ValueError("WebView2 operator remediation packet root must stay inside the vault workspace") from exc
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


def build_webview2_operator_remediation_packet(
    vault_root: str | Path,
    *,
    host_remediation_report_path: str | Path | None = None,
    remediation_evidence_path: str | Path | None = None,
    post_remediation_readiness_path: str | Path | None = None,
) -> dict[str, Any]:
    """Build a single operator packet without repairing WebView2 or executing reruns."""

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
    readiness_loaded = _load_report(
        vault,
        post_remediation_readiness_path,
        POST_REMEDIATION_READINESS_ROOT,
        "studio_webview2_post_remediation_rerun_readiness",
    )

    host_payload = host_loaded.get("payload") or {}
    evidence_payload = evidence_loaded.get("payload") or {}
    readiness_payload = readiness_loaded.get("payload") or {}
    host_authority = _review_only_authority(host_payload) if host_loaded.get("artifact_present") else False
    evidence_authority = _review_only_authority(evidence_payload) if evidence_loaded.get("artifact_present") else False
    readiness_authority = _review_only_authority(readiness_payload) if readiness_loaded.get("artifact_present") else False
    evidence_readiness = evidence_payload.get("readiness") or {}
    evidence_remediation = evidence_payload.get("remediation") or {}
    rerun_plan = readiness_payload.get("rerun_plan") or {}
    operator_handoff = host_payload.get("operator_handoff") or {}
    rerun_ready = bool(readiness_payload.get("ok")) and bool(rerun_plan.get("ready"))

    blockers: list[str] = []
    if not host_loaded.get("ok"):
        blockers.append("WebView2 runtime host-remediation handoff/report is missing or invalid.")
    if host_loaded.get("artifact_present") and not host_authority:
        blockers.append("WebView2 host-remediation handoff authority boundary is not acceptable.")
    if not evidence_loaded.get("ok"):
        blockers.append("WebView2 runtime remediation evidence report is missing or invalid.")
    if evidence_loaded.get("artifact_present") and not evidence_authority:
        blockers.append("WebView2 runtime remediation evidence authority boundary is not acceptable.")
    if not readiness_loaded.get("ok"):
        blockers.append("WebView2 post-remediation rerun-readiness report is missing or invalid.")
    if readiness_loaded.get("artifact_present") and not readiness_authority:
        blockers.append("WebView2 post-remediation rerun-readiness authority boundary is not acceptable.")

    ok = not blockers
    if not ok:
        status = "blocked_webview2_operator_remediation_packet"
    elif rerun_ready:
        status = "webview2_operator_remediation_packet_rerun_ready"
    else:
        status = "webview2_operator_remediation_packet_ready_for_operator"

    evidence_command = (
        "python -m runtime.cli.main studio webview2-runtime-remediation-evidence "
        "--remediation-status performed --operator \"<operator-or-role>\" "
        "--remediation-summary \"<what changed>\" --evidence-reference \"<ticket-note-or-command-output>\" "
        "--webview2-version \"<version-after-remediation>\" --remediation-timestamp \"<timestamp>\" "
        "--write-report --json"
    )
    evidence_file_command = (
        "python -m runtime.cli.main studio webview2-runtime-remediation-evidence "
        "--evidence-file <operator-webview2-remediation-evidence.json> --write-report --json"
    )
    readiness_command = (
        "python -m runtime.cli.main studio webview2-post-remediation-rerun-readiness "
        f"--host-remediation-report-path {host_loaded.get('path') or '<host-remediation.json>'} "
        "--remediation-evidence-path <performed-remediation-evidence.json> --write-report --json"
    )

    return {
        "ok": ok,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "status": status,
        "generated_at": _now_utc(),
        "vault_root": str(vault),
        "source_reports": {
            "host_remediation_handoff": {
                "path": host_loaded.get("path"),
                "artifact_present": host_loaded.get("artifact_present"),
                "loaded": host_loaded.get("ok"),
                "status": host_payload.get("status"),
                "authority_boundary_present": host_authority,
            },
            "remediation_evidence": {
                "path": evidence_loaded.get("path"),
                "artifact_present": evidence_loaded.get("artifact_present"),
                "loaded": evidence_loaded.get("ok"),
                "status": evidence_payload.get("status"),
                "remediation_status": evidence_remediation.get("status"),
                "operator_remediation_evidence_supplied": bool(
                    evidence_readiness.get("operator_remediation_evidence_supplied")
                ),
                "authority_boundary_present": evidence_authority,
            },
            "post_remediation_rerun_readiness": {
                "path": readiness_loaded.get("path"),
                "artifact_present": readiness_loaded.get("artifact_present"),
                "loaded": readiness_loaded.get("ok"),
                "status": readiness_payload.get("status"),
                "rerun_ready": rerun_ready,
                "authority_boundary_present": readiness_authority,
            },
        },
        "operator_packet": {
            "purpose": (
                "Give the operator/admin one review-only packet for external WebView2 remediation, "
                "evidence intake, and gated Pass 10B rerun sequencing."
            ),
            "required_external_actions": operator_handoff.get("required_external_actions") or [],
            "required_operator_evidence_fields": [
                "remediation_status=performed",
                "operator or host-admin role",
                "remediation_summary",
                "evidence_reference",
                "webview2_version after remediation when available",
                "remediation_timestamp when available",
            ],
            "evidence_intake_command": evidence_command,
            "evidence_file_intake_command": evidence_file_command,
            "evidence_file_template": {
                "remediation_status": "performed",
                "operator": "<operator-or-host-admin-role>",
                "remediation_summary": "<what changed outside ChaseOS>",
                "evidence_reference": "<ticket-note-command-output-or-admin-attestation>",
                "webview2_version": "<version-after-remediation-if-known>",
                "remediation_timestamp": "<timestamp-if-known>",
            },
            "post_remediation_readiness_command": readiness_command,
            "acceptance_criteria": operator_handoff.get("acceptance_criteria") or [],
            "rerun_gate": {
                "ready": rerun_ready,
                "current_status": readiness_payload.get("status"),
                "current_blockers": readiness_payload.get("blockers") or [],
                "minimal_repro_command": rerun_plan.get("minimal_repro_command"),
                "packaged_visual_qa_command": rerun_plan.get("packaged_visual_qa_command"),
                "completion_audit_command": rerun_plan.get("completion_audit_command"),
                "instruction": (
                    "Do not execute reruns until post-remediation readiness reports ready=true."
                    if not rerun_ready
                    else "Reruns are permitted by the readiness gate; execute in the recorded order."
                ),
            },
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
            {"name": "post_remediation_readiness_loaded", "ok": bool(readiness_loaded.get("ok")), "detail": readiness_loaded.get("path")},
            {"name": "post_remediation_readiness_review_only", "ok": readiness_authority, "detail": readiness_payload.get("authority")},
            {"name": "rerun_gate_ready", "ok": rerun_ready, "detail": readiness_payload.get("status")},
            {"name": "packet_review_only_boundary", "ok": True, "detail": "packet writes evidence only and performs no host mutation or rerun execution"},
        ],
        "blockers": blockers,
        "unverified": [
            "This packet does not perform WebView2 repair or reinstall.",
            "This packet does not verify the remediation effect.",
            "This packet does not execute the minimal repro, packaged visual QA, or completion audit.",
            "Pass 10B remains blocked until performed operator/admin evidence and fresh rerun proof are supplied.",
        ],
        "next_recommended_pass": (
            readiness_payload.get("next_recommended_pass")
            or "operator-remediate-webview2-runtime-then-pass10b-minimal-repro-rerun"
        ),
    }


def format_webview2_operator_remediation_packet(report: dict[str, Any]) -> str:
    sources = report.get("source_reports") or {}
    readiness = sources.get("post_remediation_rerun_readiness") or {}
    lines = [
        f"WebView2 operator remediation packet: {report.get('status')}",
        f"  ok: {report.get('ok')}",
        f"  host_handoff: {(sources.get('host_remediation_handoff') or {}).get('path')}",
        f"  evidence: {(sources.get('remediation_evidence') or {}).get('path')}",
        f"  rerun_readiness: {readiness.get('path')}",
        f"  rerun_ready: {readiness.get('rerun_ready')}",
        f"  next: {report.get('next_recommended_pass')}",
    ]
    for blocker in report.get("blockers") or []:
        lines.append(f"  blocker: {blocker}")
    return "\n".join(lines)


def write_webview2_operator_remediation_packet(
    vault_root: str | Path,
    report: dict[str, Any],
    *,
    report_slug: str | None = None,
    report_root: str | Path | None = None,
) -> dict[str, Any]:
    """Write the review-only operator packet inside the vault workspace."""

    vault = _vault_path(vault_root)
    root = _resolve_report_root(vault, report_root)
    slug = report_slug or f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}-webview2-operator-remediation-packet"
    if slug.endswith(".json"):
        slug = slug[:-5]
    json_path = (root / f"{slug}.json").resolve()
    markdown_path = (root / f"{slug}.md").resolve()
    for path in (json_path, markdown_path):
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise ValueError("WebView2 operator remediation packet output must stay inside the report root") from exc
    root.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")

    packet = report.get("operator_packet") or {}
    rerun_gate = packet.get("rerun_gate") or {}
    sources = report.get("source_reports") or {}
    lines = [
        "# WebView2 Operator Remediation Packet",
        "",
        f"Generated: {report.get('generated_at')}",
        "Runtime: Codex",
        f"Status: {report.get('status')}",
        f"OK: {report.get('ok')}",
        f"Next recommended pass: {report.get('next_recommended_pass')}",
        "",
        "## Source Reports",
        "",
        f"- Host remediation handoff: {(sources.get('host_remediation_handoff') or {}).get('path')}",
        f"- Remediation evidence: {(sources.get('remediation_evidence') or {}).get('path')}",
        f"- Post-remediation readiness: {(sources.get('post_remediation_rerun_readiness') or {}).get('path')}",
        "",
        "## Required External Actions",
        "",
    ]
    lines.extend(f"- {item}" for item in packet.get("required_external_actions") or [])
    lines.extend(["", "## Required Operator Evidence Fields", ""])
    lines.extend(f"- {item}" for item in packet.get("required_operator_evidence_fields") or [])
    lines.extend(
        [
            "",
            "## Commands",
            "",
            f"- Evidence intake: `{packet.get('evidence_intake_command')}`",
            f"- Evidence file intake: `{packet.get('evidence_file_intake_command')}`",
            f"- Post-remediation readiness: `{packet.get('post_remediation_readiness_command')}`",
            "",
            "## Rerun Gate",
            "",
            f"- Ready: {rerun_gate.get('ready')}",
            f"- Current status: {rerun_gate.get('current_status')}",
            f"- Instruction: {rerun_gate.get('instruction')}",
            f"- Minimal repro: `{rerun_gate.get('minimal_repro_command')}`",
            f"- Packaged visual QA: `{rerun_gate.get('packaged_visual_qa_command')}`",
            f"- Completion audit: `{rerun_gate.get('completion_audit_command')}`",
            "",
            "## Current Blockers",
            "",
        ]
    )
    blockers = rerun_gate.get("current_blockers") or report.get("blockers") or []
    lines.extend(f"- {blocker}" for blocker in blockers) if blockers else lines.append("- None")
    lines.extend(["", "## Acceptance Criteria", ""])
    lines.extend(f"- {item}" for item in packet.get("acceptance_criteria") or [])
    lines.extend(
        [
            "",
            "## Authority Boundary",
            "",
            "- This packet is review-only and writes packet evidence only.",
            "- It does not install or repair WebView2, mutate host policy, execute reruns, launch packaged apps, capture screenshots, sign or allowlist files, write installer/startup state, execute approvals, call providers/connectors, write Agent Bus tasks, or mutate canonical state.",
            "",
        ]
    )
    markdown_path.write_text("\n".join(lines), encoding="utf-8")
    return {
        "written": True,
        "json_path": _relative_to_vault(vault, json_path),
        "markdown_path": _relative_to_vault(vault, markdown_path),
    }
