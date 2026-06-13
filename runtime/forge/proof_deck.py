"""Chaser Forge proof-deck generator.

The proof deck is a log-only packaging surface over existing Forge evidence.
It reads repo-local build logs, docs, and visual QA reports, then optionally
writes Markdown/JSON artifacts under 07_LOGS/Workflow-Proofs. It does not make
approval decisions, consume approvals, execute Forge lifecycle actions, or
mutate canonical state.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
from typing import Any


PROOF_DECK_SCHEMA_VERSION = "forge.proof_deck.v1"
PROOF_DECK_SURFACE_ID = "chaser_forge_proof_deck"
DEFAULT_SLUG = "2026-05-21_chaser-forge-marketplace-proof-deck"
OUTPUT_ROOT = Path("07_LOGS") / "Workflow-Proofs"
NEXT_RECOMMENDED_PASS = "operator-authorize-live-url-fetch-verification-or-external-registry-publication"

BUILD_LOG_RELATIVE_PATHS = (
    Path("07_LOGS/Build-Logs/2026-05-20-ChaseOS-chaser-forge-mvp-foundation.md"),
    Path("07_LOGS/Build-Logs/2026-05-20-ChaseOS-chaser-forge-registry-and-sandbox-approval.md"),
    Path("07_LOGS/Build-Logs/2026-05-20-ChaseOS-chaser-forge-sandbox-approved-registry-writer.md"),
    Path("07_LOGS/Build-Logs/2026-05-20-ChaseOS-chaser-forge-live-install-approval-packet.md"),
    Path("07_LOGS/Build-Logs/2026-05-20-ChaseOS-chaser-forge-live-install-executor.md"),
    Path("07_LOGS/Build-Logs/2026-05-20-ChaseOS-chaser-forge-rollback-executor.md"),
    Path("07_LOGS/Build-Logs/2026-05-20-ChaseOS-chaser-forge-approval-center-routing.md"),
    Path("07_LOGS/Build-Logs/2026-05-20-ChaseOS-chaser-forge-manual-ui-lifecycle-proof.md"),
    Path("07_LOGS/Build-Logs/2026-05-20-ChaseOS-chaser-forge-proof-deck.md"),
    Path("07_LOGS/Build-Logs/2026-05-20-ChaseOS-chaser-forge-proof-deck-studio-clickthrough.md"),
    Path("07_LOGS/Build-Logs/2026-05-20-ChaseOS-chaser-forge-approval-center-decision-handoff.md"),
    Path("07_LOGS/Build-Logs/2026-05-20-ChaseOS-chaser-forge-operator-decision-form.md"),
    Path("07_LOGS/Build-Logs/2026-05-20-ChaseOS-chaser-forge-decision-bound-executor-consumption-proof.md"),
    Path("07_LOGS/Build-Logs/2026-05-20-ChaseOS-chaser-forge-marketplace-import-export-foundation.md"),
    Path("07_LOGS/Build-Logs/2026-05-20-ChaseOS-chaser-forge-marketplace-package-approval-or-import-sandbox-request.md"),
    Path("07_LOGS/Build-Logs/2026-05-20-ChaseOS-chaser-forge-marketplace-import-decision-or-sandbox-request-consumption.md"),
    Path("07_LOGS/Build-Logs/2026-05-20-ChaseOS-chaser-forge-marketplace-import-to-sandbox-approval-visual-qa.md"),
    Path("07_LOGS/Build-Logs/2026-05-21-ChaseOS-chaser-forge-no-deferrals-studio-marketplace.md"),
    Path("07_LOGS/Build-Logs/2026-05-22-ChaseOS-chaser-forge-marketplace-operator-use-closeout.md"),
    Path("07_LOGS/Build-Logs/2026-05-22-ChaseOS-chaser-forge-local-marketplace-studio-use.md"),
    Path("07_LOGS/Build-Logs/2026-05-22-ChaseOS-chaser-forge-remote-distribution-foundation.md"),
    Path("07_LOGS/Build-Logs/2026-05-22-ChaseOS-chaser-forge-hosted-marketplace-export-bundle.md"),
    Path("07_LOGS/Build-Logs/2026-05-23-ChaseOS-chaser-forge-static-host-publication-proof.md"),
    Path("07_LOGS/Build-Logs/2026-05-23-ChaseOS-chaser-forge-manual-static-host-upload-handoff.md"),
    Path("07_LOGS/Build-Logs/2026-05-23-ChaseOS-chaser-forge-static-host-upload-receipt-proof.md"),
    Path("07_LOGS/Build-Logs/2026-05-24-ChaseOS-chaser-forge-published-static-index-registration.md"),
)

DOC_RELATIVE_PATHS = (
    Path("runtime/forge/README.md"),
    Path("docs/features/chaser_forge_mvp_extension_install_contract.md"),
    Path("06_AGENTS/ChaseOS-Approval-Center.md"),
)

VISUAL_QA_REPORT_RELATIVE_PATH = Path(
    "07_LOGS/Studio-Visual-QA/2026-05-20-chaser-forge-approval-center-lifecycle-proof/"
    "chaser-forge-approval-center-lifecycle-report.json"
)

STUDIO_CLICKTHROUGH_REPORT_RELATIVE_PATH = Path(
    "07_LOGS/Studio-Visual-QA/2026-05-21-chaser-forge-marketplace-proof-deck-clickthrough/"
    "chaser-forge-proof-deck-clickthrough-report.json"
)

MARKETPLACE_BRIDGE_VISUAL_QA_REPORT_RELATIVE_PATH = Path(
    "07_LOGS/Studio-Visual-QA/2026-05-21-chaser-forge-marketplace-publish-install-visual-qa/"
    "chaser-forge-marketplace-import-bridge-visual-qa-report.json"
)
MARKETPLACE_BRIDGE_VISUAL_QA_FALLBACK_REPORT_RELATIVE_PATH = Path(
    "07_LOGS/Studio-Visual-QA/chaser-forge-marketplace-bridge-visual-qa-report.json"
)

LIVE_STUDIO_CONTROL_PROOF_REPORT_RELATIVE_PATH = Path(
    "07_LOGS/Studio-Visual-QA/2026-05-21-chaser-forge-marketplace-live-studio-control-proof/"
    "chaser-forge-live-studio-control-proof-report.json"
)
LIVE_STUDIO_CONTROL_PROOF_FALLBACK_REPORT_RELATIVE_PATH = Path(
    "07_LOGS/Studio-Visual-QA/chaser-forge-live-studio-control-proof-report.json"
)

OPERATOR_USE_STUDIO_PROOF_REPORT_RELATIVE_PATH = Path(
    "07_LOGS/Studio-Visual-QA/2026-05-21-chaser-forge-marketplace-operator-use-studio-proof/"
    "chaser-forge-marketplace-operator-use-visual-qa-report.json"
)
OPERATOR_USE_CLOSEOUT_SMOKE_RESULT_RELATIVE_PATH = Path(
    "07_LOGS/Studio-Visual-QA/2026-05-22-chaser-forge-marketplace-operator-use-closeout-smoke/"
    "chaser-forge-marketplace-operator-use-closeout-smoke-result.json"
)
LOCAL_MARKETPLACE_LIBRARY_SMOKE_RESULT_RELATIVE_PATH = Path(
    "07_LOGS/Studio-Visual-QA/2026-05-22-chaser-forge-local-marketplace-library-studio-use-smoke/"
    "chaser-forge-local-marketplace-library-studio-use-smoke-result.json"
)
REMOTE_DISTRIBUTION_SMOKE_RESULT_RELATIVE_PATH = Path(
    "07_LOGS/Studio-Visual-QA/2026-05-22-chaser-forge-remote-distribution-foundation-smoke/"
    "chaser-forge-remote-distribution-foundation-smoke-result.json"
)
HOSTED_MARKETPLACE_EXPORT_BUNDLE_SMOKE_RESULT_RELATIVE_PATH = Path(
    "07_LOGS/Studio-Visual-QA/2026-05-22-chaser-forge-hosted-marketplace-export-bundle-smoke/"
    "chaser-forge-hosted-marketplace-export-bundle-smoke-result.json"
)
STATIC_HOST_PUBLICATION_SMOKE_RESULT_RELATIVE_PATH = Path(
    "07_LOGS/Studio-Visual-QA/2026-05-23-chaser-forge-static-host-publication-proof-smoke/"
    "chaser-forge-static-host-publication-proof-smoke-result.json"
)
STATIC_UPLOAD_HANDOFF_SMOKE_RESULT_RELATIVE_PATH = Path(
    "07_LOGS/Studio-Visual-QA/2026-05-23-chaser-forge-static-upload-handoff-smoke/"
    "chaser-forge-static-upload-handoff-smoke-result.json"
)
STATIC_UPLOAD_RECEIPT_SMOKE_RESULT_RELATIVE_PATH = Path(
    "07_LOGS/Studio-Visual-QA/2026-05-23-chaser-forge-static-upload-receipt-smoke/"
    "chaser-forge-static-upload-receipt-smoke-result.json"
)
PUBLISHED_STATIC_INDEX_REGISTRATION_SMOKE_RESULT_RELATIVE_PATH = Path(
    "07_LOGS/Studio-Visual-QA/2026-05-24-chaser-forge-published-static-index-registration-smoke/"
    "chaser-forge-published-static-index-registration-smoke-result.json"
)

REQUIRED_LIFECYCLE_STATUSES = {
    "pending_operator_review",
    "approved_pending_execution",
    "consumed",
    "rejected",
    "invalid_packet",
}

FORBIDDEN_AUTHORITY_FLAGS = (
    "approval_decision_allowed",
    "approval_artifact_write_allowed",
    "approval_consumption_allowed",
    "approval_execution_allowed",
    "forge_sandbox_install_allowed",
    "forge_live_install_allowed",
    "forge_rollback_allowed",
    "forge_registry_mutation_allowed",
    "extension_file_write_allowed",
    "extension_file_delete_allowed",
    "protected_core_mutation_allowed",
    "provider_calls_allowed",
    "model_calls_allowed",
    "schedule_activation_allowed",
    "agent_bus_task_write_allowed",
    "secret_or_credential_read_allowed",
    "pulse_memory_mutation_allowed",
    "personal_map_mutation_allowed",
    "rnd_truth_state_mutation_allowed",
    "canonical_mutation_allowed",
)


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _safe_slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-")
    if not slug or slug in {".", ".."} or ".." in slug:
        raise ValueError("proof deck slug is invalid")
    return slug


def _assert_inside(child: Path, parent: Path) -> None:
    child_resolved = child.resolve()
    parent_resolved = parent.resolve()
    try:
        child_resolved.relative_to(parent_resolved)
    except ValueError as exc:
        raise ValueError("Forge proof-deck artifacts must stay inside 07_LOGS/Workflow-Proofs") from exc


def _relative_to_vault(vault: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(vault.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def _io_path(path: Path) -> Path:
    resolved = path.resolve()
    if os.name == "nt" and not str(resolved).startswith("\\\\?\\"):
        return Path("\\\\?\\" + str(resolved))
    return resolved


def _is_file(path: Path) -> bool:
    try:
        return _io_path(path).is_file()
    except OSError:
        return False


def _write_text(path: Path, text: str) -> None:
    target = _io_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def _read_text(path: Path) -> str:
    try:
        return _io_path(path).read_text(encoding="utf-8")
    except OSError:
        return ""


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(_io_path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _marketplace_bridge_report_path(vault: Path) -> tuple[Path, Path]:
    canonical = vault / MARKETPLACE_BRIDGE_VISUAL_QA_REPORT_RELATIVE_PATH
    if _is_file(canonical):
        return MARKETPLACE_BRIDGE_VISUAL_QA_REPORT_RELATIVE_PATH, canonical
    fallback = vault / MARKETPLACE_BRIDGE_VISUAL_QA_FALLBACK_REPORT_RELATIVE_PATH
    if _is_file(fallback):
        return MARKETPLACE_BRIDGE_VISUAL_QA_FALLBACK_REPORT_RELATIVE_PATH, fallback
    return MARKETPLACE_BRIDGE_VISUAL_QA_REPORT_RELATIVE_PATH, canonical


def _live_studio_control_report_path(vault: Path) -> tuple[Path, Path]:
    canonical = vault / LIVE_STUDIO_CONTROL_PROOF_REPORT_RELATIVE_PATH
    if _is_file(canonical):
        return LIVE_STUDIO_CONTROL_PROOF_REPORT_RELATIVE_PATH, canonical
    fallback = vault / LIVE_STUDIO_CONTROL_PROOF_FALLBACK_REPORT_RELATIVE_PATH
    if _is_file(fallback):
        return LIVE_STUDIO_CONTROL_PROOF_FALLBACK_REPORT_RELATIVE_PATH, fallback
    return LIVE_STUDIO_CONTROL_PROOF_REPORT_RELATIVE_PATH, canonical


def _operator_use_studio_report_path(vault: Path) -> tuple[Path, Path]:
    canonical = vault / OPERATOR_USE_STUDIO_PROOF_REPORT_RELATIVE_PATH
    return OPERATOR_USE_STUDIO_PROOF_REPORT_RELATIVE_PATH, canonical


def _operator_use_closeout_smoke_result_path(vault: Path) -> tuple[Path, Path]:
    canonical = vault / OPERATOR_USE_CLOSEOUT_SMOKE_RESULT_RELATIVE_PATH
    return OPERATOR_USE_CLOSEOUT_SMOKE_RESULT_RELATIVE_PATH, canonical


def _local_marketplace_library_smoke_result_path(vault: Path) -> tuple[Path, Path]:
    canonical = vault / LOCAL_MARKETPLACE_LIBRARY_SMOKE_RESULT_RELATIVE_PATH
    return LOCAL_MARKETPLACE_LIBRARY_SMOKE_RESULT_RELATIVE_PATH, canonical


def _remote_distribution_smoke_result_path(vault: Path) -> tuple[Path, Path]:
    canonical = vault / REMOTE_DISTRIBUTION_SMOKE_RESULT_RELATIVE_PATH
    return REMOTE_DISTRIBUTION_SMOKE_RESULT_RELATIVE_PATH, canonical


def _hosted_marketplace_export_bundle_smoke_result_path(vault: Path) -> tuple[Path, Path]:
    canonical = vault / HOSTED_MARKETPLACE_EXPORT_BUNDLE_SMOKE_RESULT_RELATIVE_PATH
    return HOSTED_MARKETPLACE_EXPORT_BUNDLE_SMOKE_RESULT_RELATIVE_PATH, canonical


def _static_host_publication_smoke_result_path(vault: Path) -> tuple[Path, Path]:
    canonical = vault / STATIC_HOST_PUBLICATION_SMOKE_RESULT_RELATIVE_PATH
    return STATIC_HOST_PUBLICATION_SMOKE_RESULT_RELATIVE_PATH, canonical


def _static_upload_handoff_smoke_result_path(vault: Path) -> tuple[Path, Path]:
    canonical = vault / STATIC_UPLOAD_HANDOFF_SMOKE_RESULT_RELATIVE_PATH
    return STATIC_UPLOAD_HANDOFF_SMOKE_RESULT_RELATIVE_PATH, canonical


def _static_upload_receipt_smoke_result_path(vault: Path) -> tuple[Path, Path]:
    canonical = vault / STATIC_UPLOAD_RECEIPT_SMOKE_RESULT_RELATIVE_PATH
    return STATIC_UPLOAD_RECEIPT_SMOKE_RESULT_RELATIVE_PATH, canonical


def _published_static_index_registration_smoke_result_path(vault: Path) -> tuple[Path, Path]:
    canonical = vault / PUBLISHED_STATIC_INDEX_REGISTRATION_SMOKE_RESULT_RELATIVE_PATH
    return PUBLISHED_STATIC_INDEX_REGISTRATION_SMOKE_RESULT_RELATIVE_PATH, canonical


def _extract_status(text: str) -> str:
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("- Status:"):
            return line.split(":", 1)[1].strip()
        if line.startswith("Status:"):
            return line.split(":", 1)[1].strip()
        if line.startswith("status:"):
            return line.split(":", 1)[1].strip()
    return "status_not_found"


def _evidence_item(
    vault: Path,
    relative_path: Path,
    *,
    kind: str,
    summary: str,
    required: bool = True,
) -> dict[str, Any]:
    path = vault / relative_path
    text = _read_text(path) if _is_file(path) and relative_path.suffix.lower() == ".md" else ""
    return {
        "kind": kind,
        "path": relative_path.as_posix(),
        "exists": _is_file(path),
        "required": required,
        "summary": summary,
        "status_hint": _extract_status(text) if text else "",
    }


def _build_log_summary(path: Path) -> str:
    name = path.stem
    return name.replace("2026-05-20-ChaseOS-", "").replace("-", " ")


def _visual_report_summary(vault: Path) -> tuple[dict[str, Any], list[str], list[dict[str, Any]]]:
    report_path = vault / VISUAL_QA_REPORT_RELATIVE_PATH
    payload = _read_json(report_path)
    blockers: list[str] = []
    screenshot_refs: list[dict[str, Any]] = []
    if payload is None:
        return (
            {
                "report_path": VISUAL_QA_REPORT_RELATIVE_PATH.as_posix(),
                "report_exists": _is_file(report_path),
                "ok": False,
                "status": "missing_or_unreadable_visual_qa_report",
                "lifecycle_statuses": [],
                "status_counts": {},
                "desktop_and_mobile_checked": False,
                "source_group_visible": False,
                "lifecycle_tokens_visible": False,
                "fixture_vault_persisted": None,
                "screenshots": [],
            },
            ["visual_qa_report_missing_or_unreadable"],
            screenshot_refs,
        )

    if payload.get("ok") is not True:
        blockers.append("visual_qa_report_not_ok")
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    source_group = payload.get("forge_source_group") if isinstance(payload.get("forge_source_group"), dict) else {}
    lifecycle_statuses = set(str(item) for item in summary.get("lifecycle_statuses") or [])
    missing_statuses = sorted(REQUIRED_LIFECYCLE_STATUSES - lifecycle_statuses)
    if missing_statuses:
        blockers.append("visual_qa_missing_required_lifecycle_statuses")
    if summary.get("source_group_visible") is not True:
        blockers.append("visual_qa_source_group_not_visible")
    if summary.get("lifecycle_tokens_visible") is not True:
        blockers.append("visual_qa_lifecycle_tokens_not_visible")
    if summary.get("desktop_and_mobile_checked") is not True:
        blockers.append("visual_qa_desktop_mobile_not_checked")
    if summary.get("framework_overlay_detected") is True:
        blockers.append("visual_qa_framework_overlay_detected")
    if summary.get("console_errors_or_warnings"):
        blockers.append("visual_qa_console_errors_or_warnings")

    evidence = payload.get("evidence") if isinstance(payload.get("evidence"), dict) else {}
    screenshots = evidence.get("screenshots") if isinstance(evidence.get("screenshots"), list) else []
    if len(screenshots) < 2:
        blockers.append("visual_qa_missing_desktop_or_mobile_screenshot")
    for shot in screenshots:
        if not isinstance(shot, dict):
            continue
        rel_path = Path(str(shot.get("path") or ""))
        exists = bool(str(rel_path)) and _is_file(vault / rel_path)
        if not exists:
            blockers.append("visual_qa_screenshot_file_missing")
        if shot.get("not_blank") is not True:
            blockers.append("visual_qa_screenshot_blank_or_unverified")
        if shot.get("source_group_visible") is not True:
            blockers.append("visual_qa_screenshot_source_group_not_visible")
        screenshot_refs.append(
            {
                "viewport": shot.get("viewport"),
                "path": rel_path.as_posix() if str(rel_path) else "",
                "exists": exists,
                "bytes": shot.get("bytes"),
                "not_blank": shot.get("not_blank"),
                "source_group_visible": shot.get("source_group_visible"),
                "missing_lifecycle_tokens": list(shot.get("missing_lifecycle_tokens") or []),
            }
        )

    return (
        {
            "report_path": VISUAL_QA_REPORT_RELATIVE_PATH.as_posix(),
            "report_exists": _is_file(report_path),
            "ok": bool(payload.get("ok")),
            "status": payload.get("status") or "status_not_found",
            "lifecycle_statuses": sorted(lifecycle_statuses),
            "required_lifecycle_statuses": sorted(REQUIRED_LIFECYCLE_STATUSES),
            "missing_lifecycle_statuses": missing_statuses,
            "status_counts": source_group.get("status_counts") or {},
            "artifact_count": source_group.get("artifact_count") or summary.get("artifact_count"),
            "pending_count": source_group.get("pending_count") or summary.get("pending_count"),
            "ready_count": source_group.get("ready_count") or summary.get("ready_count"),
            "blocked_count": source_group.get("blocked_count") or summary.get("blocked_count"),
            "desktop_and_mobile_checked": bool(summary.get("desktop_and_mobile_checked")),
            "source_group_visible": bool(summary.get("source_group_visible")),
            "lifecycle_tokens_visible": bool(summary.get("lifecycle_tokens_visible")),
            "fixture_vault_persisted": evidence.get("fixture_vault_persisted"),
            "screenshots": screenshot_refs,
            "browser_fallback_reason": summary.get("browser_fallback_reason") or "",
        },
        list(dict.fromkeys(blockers)),
        screenshot_refs,
    )


def _studio_clickthrough_summary(vault: Path) -> tuple[dict[str, Any], list[str], list[dict[str, Any]]]:
    report_path = vault / STUDIO_CLICKTHROUGH_REPORT_RELATIVE_PATH
    payload = _read_json(report_path)
    blockers: list[str] = []
    screenshot_refs: list[dict[str, Any]] = []
    if payload is None:
        return (
            {
                "report_path": STUDIO_CLICKTHROUGH_REPORT_RELATIVE_PATH.as_posix(),
                "report_exists": _is_file(report_path),
                "ok": False,
                "status": "missing_or_unreadable_studio_clickthrough_report",
                "proof_deck_section_visible": False,
                "missing_required_tokens": [],
                "screenshots": [],
            },
            [],
            screenshot_refs,
        )

    if payload.get("ok") is not True:
        blockers.append("studio_clickthrough_report_not_ok")
    missing_tokens = list(payload.get("missing_required_tokens") or [])
    if missing_tokens:
        blockers.append("studio_clickthrough_missing_required_tokens")
    if payload.get("console_errors_or_warnings"):
        blockers.append("studio_clickthrough_console_errors_or_warnings")
    if payload.get("page_errors"):
        blockers.append("studio_clickthrough_page_errors")

    screenshots = payload.get("screenshots") if isinstance(payload.get("screenshots"), list) else []
    if len(screenshots) < 2:
        blockers.append("studio_clickthrough_missing_desktop_or_mobile_screenshot")
    for shot in screenshots:
        if not isinstance(shot, dict):
            continue
        rel_path = Path(str(shot.get("path") or ""))
        exists = bool(str(rel_path)) and _is_file(vault / rel_path)
        if not exists:
            blockers.append("studio_clickthrough_screenshot_file_missing")
        if shot.get("not_blank") is not True:
            blockers.append("studio_clickthrough_screenshot_blank_or_unverified")
        if shot.get("proof_deck_section_visible") is not True:
            blockers.append("studio_clickthrough_proof_deck_section_not_visible")
        if shot.get("missing_required_tokens"):
            blockers.append("studio_clickthrough_screenshot_missing_required_tokens")
        screenshot_refs.append(
            {
                "viewport": shot.get("viewport"),
                "path": rel_path.as_posix() if str(rel_path) else "",
                "exists": exists,
                "bytes": shot.get("bytes"),
                "not_blank": shot.get("not_blank"),
                "proof_deck_section_visible": shot.get("proof_deck_section_visible"),
                "missing_required_tokens": list(shot.get("missing_required_tokens") or []),
            }
        )

    return (
        {
            "report_path": STUDIO_CLICKTHROUGH_REPORT_RELATIVE_PATH.as_posix(),
            "report_exists": _is_file(report_path),
            "ok": bool(payload.get("ok")),
            "status": payload.get("status") or "status_not_found",
            "proof_deck_status": payload.get("proof_deck_status"),
            "proof_deck_markdown_path": payload.get("proof_deck_markdown_path"),
            "proof_deck_json_path": payload.get("proof_deck_json_path"),
            "proof_deck_read_only": payload.get("proof_deck_read_only"),
            "missing_required_tokens": missing_tokens,
            "screenshots": screenshot_refs,
            "proof_deck_section_visible": all(bool(shot.get("proof_deck_section_visible")) for shot in screenshot_refs),
        },
        list(dict.fromkeys(blockers)),
        screenshot_refs,
    )


def _marketplace_bridge_visual_summary(vault: Path) -> tuple[dict[str, Any], list[str], list[dict[str, Any]]]:
    report_relative_path, report_path = _marketplace_bridge_report_path(vault)
    payload = _read_json(report_path)
    blockers: list[str] = []
    screenshot_refs: list[dict[str, Any]] = []
    if payload is None:
        return (
            {
                "report_path": report_relative_path.as_posix(),
                "report_exists": _is_file(report_path),
                "ok": False,
                "status": "missing_or_unreadable_marketplace_bridge_visual_qa_report",
                "marketplace_section_visible": False,
                "bridge_api_tokens_visible": False,
                "bridge_written_state_visible": False,
                "desktop_and_mobile_checked": False,
                "sandbox_approval_request_written": None,
                "marketplace_import_approval_consumed": None,
                "sandbox_approval_consumed": None,
                "registry_written": None,
                "extension_files_written": None,
                "exact_once_marker_reserved": None,
                "screenshots": [],
            },
            ["marketplace_bridge_visual_qa_report_missing_or_unreadable"],
            screenshot_refs,
        )

    if payload.get("ok") is not True:
        blockers.append("marketplace_bridge_visual_qa_report_not_ok")
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    fixture = payload.get("fixture_evidence") if isinstance(payload.get("fixture_evidence"), dict) else {}
    if summary.get("marketplace_section_visible") is not True:
        blockers.append("marketplace_bridge_section_not_visible")
    if summary.get("bridge_api_tokens_visible") is not True:
        blockers.append("marketplace_bridge_api_tokens_not_visible")
    if summary.get("bridge_written_state_visible") is not True:
        blockers.append("marketplace_bridge_written_state_not_visible")
    if summary.get("desktop_and_mobile_checked") is not True:
        blockers.append("marketplace_bridge_desktop_mobile_not_checked")
    if fixture.get("sandbox_approval_request_written") is not True:
        blockers.append("marketplace_bridge_sandbox_request_not_written")
    if fixture.get("marketplace_import_approval_consumed") is not False:
        blockers.append("marketplace_bridge_import_approval_consumed_unexpected")
    if fixture.get("sandbox_approval_consumed") is not False:
        blockers.append("marketplace_bridge_sandbox_approval_consumed_unexpected")
    if fixture.get("registry_written") is not False:
        blockers.append("marketplace_bridge_registry_written_unexpected")
    if fixture.get("extension_files_written") != []:
        blockers.append("marketplace_bridge_extension_files_written_unexpected")
    if fixture.get("exact_once_marker_reserved") is not False:
        blockers.append("marketplace_bridge_exact_once_marker_reserved_unexpected")
    if payload.get("missing_required_tokens"):
        blockers.append("marketplace_bridge_missing_required_tokens")
    if payload.get("console_errors_or_warnings"):
        blockers.append("marketplace_bridge_console_errors_or_warnings")
    if payload.get("page_errors"):
        blockers.append("marketplace_bridge_page_errors")

    screenshots = payload.get("screenshots") if isinstance(payload.get("screenshots"), list) else []
    if len(screenshots) < 2:
        blockers.append("marketplace_bridge_missing_desktop_or_mobile_screenshot")
    for shot in screenshots:
        if not isinstance(shot, dict):
            continue
        rel_path = Path(str(shot.get("path") or ""))
        exists = bool(str(rel_path)) and _is_file(vault / rel_path)
        if not exists:
            blockers.append("marketplace_bridge_screenshot_file_missing")
        if shot.get("not_blank") is not True:
            blockers.append("marketplace_bridge_screenshot_blank_or_unverified")
        if shot.get("marketplace_section_visible") is not True:
            blockers.append("marketplace_bridge_screenshot_section_not_visible")
        if shot.get("bridge_api_tokens_visible") is not True:
            blockers.append("marketplace_bridge_screenshot_api_tokens_not_visible")
        if shot.get("bridge_written_state_visible") is not True:
            blockers.append("marketplace_bridge_screenshot_written_state_not_visible")
        if shot.get("missing_required_tokens"):
            blockers.append("marketplace_bridge_screenshot_missing_required_tokens")
        screenshot_refs.append(
            {
                "viewport": shot.get("viewport"),
                "path": rel_path.as_posix() if str(rel_path) else "",
                "exists": exists,
                "bytes": shot.get("bytes"),
                "not_blank": shot.get("not_blank"),
                "marketplace_section_visible": shot.get("marketplace_section_visible"),
                "bridge_api_tokens_visible": shot.get("bridge_api_tokens_visible"),
                "bridge_written_state_visible": shot.get("bridge_written_state_visible"),
                "missing_required_tokens": list(shot.get("missing_required_tokens") or []),
            }
        )

    return (
        {
            "report_path": report_relative_path.as_posix(),
            "report_exists": _is_file(report_path),
            "ok": bool(payload.get("ok")),
            "status": payload.get("status") or "status_not_found",
            "marketplace_section_visible": bool(summary.get("marketplace_section_visible")),
            "bridge_api_tokens_visible": bool(summary.get("bridge_api_tokens_visible")),
            "bridge_written_state_visible": bool(summary.get("bridge_written_state_visible")),
            "desktop_and_mobile_checked": bool(summary.get("desktop_and_mobile_checked")),
            "sandbox_approval_request_written": fixture.get("sandbox_approval_request_written"),
            "sandbox_approval_artifact_path": fixture.get("sandbox_approval_artifact_path") or "",
            "marketplace_import_approval_status": fixture.get("marketplace_import_approval_status") or "",
            "marketplace_import_approval_consumed": fixture.get("marketplace_import_approval_consumed"),
            "sandbox_approval_consumed": fixture.get("sandbox_approval_consumed"),
            "registry_written": fixture.get("registry_written"),
            "extension_files_written": list(fixture.get("extension_files_written") or []),
            "exact_once_marker_reserved": fixture.get("exact_once_marker_reserved"),
            "missing_required_tokens": list(payload.get("missing_required_tokens") or []),
            "screenshots": screenshot_refs,
            "browser_fallback_reason": (payload.get("browser_availability") or {}).get("fallback_reason") or "",
        },
        list(dict.fromkeys(blockers)),
        screenshot_refs,
    )


def _live_studio_control_summary(vault: Path) -> tuple[dict[str, Any], list[str]]:
    report_relative_path, report_path = _live_studio_control_report_path(vault)
    payload = _read_json(report_path)
    blockers: list[str] = []
    if payload is None:
        return (
            {
                "report_path": report_relative_path.as_posix(),
                "report_exists": _is_file(report_path),
                "ok": False,
                "status": "missing_or_unreadable_live_studio_control_proof",
                "sandbox_registry_written": None,
                "live_install_executed": None,
                "rollback_executed": None,
                "registry_returned_to_sandbox": None,
                "package_artifact_written": None,
                "import_approval_written": None,
                "sandbox_request_written": None,
                "catalog_listing_written": None,
                "marketplace_import_approval_consumed": None,
                "marketplace_install_executed": None,
                "marketplace_install_registry_written": None,
                "marketplace_install_extension_files_written": None,
                "marketplace_install_exact_once_marker_reserved": None,
                "fixture_cleanup_completed": None,
            },
            ["live_studio_control_proof_missing_or_unreadable"],
        )

    if payload.get("ok") is not True:
        blockers.append("live_studio_control_proof_not_ok")
    lifecycle = payload.get("lifecycle_controls") if isinstance(payload.get("lifecycle_controls"), dict) else {}
    lifecycle_checks = lifecycle.get("checks") if isinstance(lifecycle.get("checks"), dict) else {}
    marketplace = payload.get("marketplace_controls") if isinstance(payload.get("marketplace_controls"), dict) else {}
    marketplace_checks = marketplace.get("checks") if isinstance(marketplace.get("checks"), dict) else {}
    bridge = marketplace.get("sandbox_request_bridge") if isinstance(marketplace.get("sandbox_request_bridge"), dict) else {}
    publish = marketplace.get("marketplace_publish") if isinstance(marketplace.get("marketplace_publish"), dict) else {}
    install = marketplace.get("marketplace_install") if isinstance(marketplace.get("marketplace_install"), dict) else {}
    fixture_policy = payload.get("fixture_policy") if isinstance(payload.get("fixture_policy"), dict) else {}

    required_lifecycle_checks = (
        "sandbox_wrong_digest_blocked",
        "sandbox_decision_recorded",
        "sandbox_ready_without_write",
        "sandbox_registry_written",
        "sandbox_approval_consumed",
        "live_wrong_digest_blocked",
        "live_decision_recorded",
        "live_ready_without_write",
        "live_install_executed",
        "live_approval_consumed",
        "rollback_wrong_digest_blocked",
        "rollback_decision_recorded",
        "rollback_ready_without_write",
        "rollback_executed",
        "rollback_approval_consumed",
        "registry_returned_to_sandbox",
        "extension_files_retained_after_rollback",
        "protected_core_mutation_blocked",
    )
    required_marketplace_checks = (
        "package_wrong_digest_blocked",
        "package_artifact_written",
        "import_preview_ok",
        "import_preview_no_install",
        "catalog_initially_readable",
        "publish_preview_ok",
        "publish_wrong_digest_blocked",
        "catalog_listing_written",
        "catalog_entry_readable",
        "import_approval_wrong_digest_blocked",
        "import_approval_written",
        "import_decision_recorded",
        "bridge_preview_ok",
        "bridge_wrong_digest_blocked",
        "sandbox_request_written",
        "sandbox_decision_recorded",
        "marketplace_install_ready_without_write",
        "marketplace_install_executed",
        "marketplace_import_approval_consumed_by_install",
        "sandbox_approval_consumed_by_install",
        "registry_written_by_marketplace_install",
        "extension_files_written_by_marketplace_install",
        "exact_once_marker_reserved_by_marketplace_install",
        "duplicate_marketplace_install_blocked",
    )
    blockers.extend(
        f"live_studio_control_lifecycle_check_failed:{name}"
        for name in required_lifecycle_checks
        if lifecycle_checks.get(name) is not True
    )
    blockers.extend(
        f"live_studio_control_marketplace_check_failed:{name}"
        for name in required_marketplace_checks
        if marketplace_checks.get(name) is not True
    )
    if fixture_policy.get("lifecycle_cleanup_completed") is not True:
        blockers.append("live_studio_control_lifecycle_fixture_not_cleaned")
    if fixture_policy.get("marketplace_cleanup_completed") is not True:
        blockers.append("live_studio_control_marketplace_fixture_not_cleaned")
    authority = payload.get("authority") if isinstance(payload.get("authority"), dict) else {}
    forbidden_authority = [
        "real_vault_forge_approval_write_allowed",
        "real_vault_registry_write_allowed",
        "real_vault_extension_file_write_allowed",
        "real_vault_exact_once_marker_write_allowed",
        "provider_or_model_call_allowed",
        "agent_bus_dispatch_allowed",
        "protected_core_mutation_allowed",
        "pulse_memory_mutation_allowed",
        "personal_map_mutation_allowed",
        "rnd_truth_state_mutation_allowed",
        "canonical_mutation_allowed",
    ]
    blockers.extend(
        f"live_studio_control_forbidden_authority_flag_true:{flag}"
        for flag in forbidden_authority
        if authority.get(flag) is not False
    )

    return (
        {
            "report_path": report_relative_path.as_posix(),
            "report_exists": _is_file(report_path),
            "ok": bool(payload.get("ok")),
            "status": payload.get("status") or "status_not_found",
            "sandbox_registry_written": lifecycle_checks.get("sandbox_registry_written"),
            "sandbox_approval_consumed": lifecycle_checks.get("sandbox_approval_consumed"),
            "live_install_executed": lifecycle_checks.get("live_install_executed"),
            "live_approval_consumed": lifecycle_checks.get("live_approval_consumed"),
            "rollback_executed": lifecycle_checks.get("rollback_executed"),
            "rollback_approval_consumed": lifecycle_checks.get("rollback_approval_consumed"),
            "registry_returned_to_sandbox": lifecycle_checks.get("registry_returned_to_sandbox"),
            "package_artifact_written": marketplace_checks.get("package_artifact_written"),
            "catalog_listing_written": marketplace_checks.get("catalog_listing_written"),
            "import_approval_written": marketplace_checks.get("import_approval_written"),
            "sandbox_request_written": marketplace_checks.get("sandbox_request_written"),
            "marketplace_import_approval_consumed": install.get("marketplace_import_approval_consumed"),
            "marketplace_bridge_registry_written": bridge.get("registry_written"),
            "marketplace_bridge_extension_files_written": list(bridge.get("extension_files_written") or []),
            "marketplace_bridge_exact_once_marker_reserved": bridge.get("exact_once_marker_reserved"),
            "marketplace_install_executed": install.get("marketplace_install_executed"),
            "marketplace_install_registry_written": install.get("registry_written"),
            "marketplace_install_extension_files_written": list(install.get("extension_files_written") or []),
            "marketplace_install_exact_once_marker_reserved": install.get("exact_once_marker_reserved"),
            "marketplace_catalog_entry_count": publish.get("catalog_entry_count"),
            "fixture_cleanup_completed": bool(
                fixture_policy.get("lifecycle_cleanup_completed")
                and fixture_policy.get("marketplace_cleanup_completed")
            ),
        },
        list(dict.fromkeys(blockers)),
    )


def _operator_use_studio_summary(vault: Path) -> tuple[dict[str, Any], list[str], list[dict[str, Any]]]:
    report_relative_path, report_path = _operator_use_studio_report_path(vault)
    payload = _read_json(report_path)
    blockers: list[str] = []
    screenshot_refs: list[dict[str, Any]] = []
    if payload is None:
        return (
            {
                "report_path": report_relative_path.as_posix(),
                "report_exists": _is_file(report_path),
                "ok": False,
                "status": "missing_or_unreadable_operator_use_studio_proof",
                "publish_status_visible_after_refresh": None,
                "install_status_visible_after_refresh": None,
                "required_api_methods_called": None,
                "operator_confirmations_accepted": None,
                "fixture_registry_written": None,
                "fixture_extension_files_written": None,
                "fixture_import_approval_consumed": None,
                "fixture_sandbox_approval_consumed": None,
                "fixture_exact_once_marker_written": None,
                "desktop_and_mobile_checked": None,
                "screenshots": [],
            },
            ["operator_use_studio_proof_missing_or_unreadable"],
            screenshot_refs,
        )

    if payload.get("ok") is not True:
        blockers.append("operator_use_studio_proof_not_ok")
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    required_summary_true = (
        "page_identity_ok",
        "publish_button_clicked",
        "install_button_clicked",
        "publish_status_visible_after_refresh",
        "install_status_visible_after_refresh",
        "required_api_methods_called",
        "desktop_and_mobile_checked",
        "screenshots_not_blank",
        "marketplace_section_visible",
        "fixture_registry_written",
        "fixture_extension_files_written",
        "fixture_import_approval_consumed",
        "fixture_sandbox_approval_consumed",
        "fixture_exact_once_marker_written",
        "fixture_cleanup_completed",
    )
    blockers.extend(
        f"operator_use_summary_check_failed:{key}" for key in required_summary_true if summary.get(key) is not True
    )
    if int(summary.get("operator_confirmations_accepted") or 0) < 2:
        blockers.append("operator_use_confirmations_not_accepted")
    if payload.get("missing_required_api_methods"):
        blockers.append("operator_use_missing_required_api_methods")
    if payload.get("console_errors_or_warnings"):
        blockers.append("operator_use_console_errors_or_warnings")
    if payload.get("page_errors"):
        blockers.append("operator_use_page_errors")
    authority = payload.get("authority") if isinstance(payload.get("authority"), dict) else {}
    forbidden_authority = (
        "real_vault_approval_artifact_write_allowed",
        "real_vault_registry_write_allowed",
        "real_vault_extension_file_write_allowed",
        "real_vault_exact_once_marker_write_allowed",
        "remote_marketplace_call_allowed",
        "third_party_package_exchange_allowed",
        "unauthorized_auto_install_allowed",
        "generic_approval_center_write_control_allowed",
        "provider_or_model_call_allowed",
        "agent_bus_dispatch_allowed",
        "protected_core_mutation_allowed",
        "pulse_memory_mutation_allowed",
        "personal_map_mutation_allowed",
        "rnd_truth_state_mutation_allowed",
        "canonical_mutation_allowed",
    )
    blockers.extend(
        f"operator_use_forbidden_authority_flag_true:{flag}"
        for flag in forbidden_authority
        if authority.get(flag) is not False
    )

    screenshots = payload.get("screenshots") if isinstance(payload.get("screenshots"), list) else []
    if len(screenshots) < 3:
        blockers.append("operator_use_missing_required_screenshots")
    for shot in screenshots:
        if not isinstance(shot, dict):
            continue
        rel_path = Path(str(shot.get("path") or ""))
        exists = bool(str(rel_path)) and _is_file(vault / rel_path)
        if not exists:
            blockers.append("operator_use_screenshot_file_missing")
        if shot.get("not_blank") is not True:
            blockers.append("operator_use_screenshot_blank_or_unverified")
        if shot.get("marketplace_section_visible") is not True:
            blockers.append("operator_use_screenshot_marketplace_section_not_visible")
        if shot.get("framework_overlay_detected"):
            blockers.append("operator_use_screenshot_framework_overlay_detected")
        screenshot_refs.append(
            {
                "step": shot.get("step"),
                "viewport": shot.get("viewport"),
                "path": rel_path.as_posix() if str(rel_path) else "",
                "exists": exists,
                "bytes": shot.get("bytes"),
                "not_blank": shot.get("not_blank"),
                "marketplace_section_visible": shot.get("marketplace_section_visible"),
                "status_text": shot.get("status_text") or "",
                "status_state": shot.get("status_state") or "",
            }
        )

    return (
        {
            "report_path": report_relative_path.as_posix(),
            "report_exists": _is_file(report_path),
            "ok": bool(payload.get("ok")),
            "status": payload.get("status") or "status_not_found",
            "publish_status_visible_after_refresh": summary.get("publish_status_visible_after_refresh"),
            "install_status_visible_after_refresh": summary.get("install_status_visible_after_refresh"),
            "required_api_methods_called": summary.get("required_api_methods_called"),
            "operator_confirmations_accepted": summary.get("operator_confirmations_accepted"),
            "fixture_registry_written": summary.get("fixture_registry_written"),
            "fixture_extension_files_written": summary.get("fixture_extension_files_written"),
            "fixture_import_approval_consumed": summary.get("fixture_import_approval_consumed"),
            "fixture_sandbox_approval_consumed": summary.get("fixture_sandbox_approval_consumed"),
            "fixture_exact_once_marker_written": summary.get("fixture_exact_once_marker_written"),
            "desktop_and_mobile_checked": summary.get("desktop_and_mobile_checked"),
            "browser_fallback_reason": (payload.get("browser_availability") or {}).get("fallback_reason") or "",
            "screenshots": screenshot_refs,
        },
        list(dict.fromkeys(blockers)),
        screenshot_refs,
    )


def _operator_use_closeout_smoke_summary(vault: Path) -> tuple[dict[str, Any], list[str]]:
    result_relative_path, result_path = _operator_use_closeout_smoke_result_path(vault)
    payload = _read_json(result_path)
    blockers: list[str] = []
    if payload is None:
        return (
            {
                "result_path": result_relative_path.as_posix(),
                "result_exists": _is_file(result_path),
                "ok": False,
                "status": "missing_or_unreadable_operator_use_closeout_smoke",
                "elapsed_seconds": None,
                "report_path": "",
                "report_exists": False,
                "failures": [],
                "checks": {},
            },
            ["operator_use_closeout_smoke_missing_or_unreadable"],
        )

    checks = payload.get("checks") if isinstance(payload.get("checks"), dict) else {}
    failures = payload.get("failures") if isinstance(payload.get("failures"), list) else []
    report_rel = Path(str(payload.get("report_path") or ""))
    report_exists = bool(str(report_rel)) and _is_file(vault / report_rel)
    if payload.get("ok") is not True:
        blockers.append("operator_use_closeout_smoke_not_ok")
    if payload.get("status") != "COMPLETE / DIRECT CLOSEOUT SMOKE VERIFIED":
        blockers.append("operator_use_closeout_smoke_status_unexpected")
    if failures:
        blockers.append("operator_use_closeout_smoke_failures_present")
    for key in (
        "report_ok",
        "publish_status_visible_after_refresh",
        "install_status_visible_after_refresh",
        "required_api_methods_called",
        "fixture_registry_written",
        "fixture_exact_once_marker_written",
        "report_written",
    ):
        if checks.get(key) is not True:
            blockers.append(f"operator_use_closeout_smoke_check_failed:{key}")
    if not report_exists:
        blockers.append("operator_use_closeout_smoke_report_missing")

    return (
        {
            "result_path": result_relative_path.as_posix(),
            "result_exists": _is_file(result_path),
            "ok": bool(payload.get("ok")),
            "status": payload.get("status") or "",
            "elapsed_seconds": payload.get("elapsed_seconds"),
            "report_path": report_rel.as_posix() if str(report_rel) else "",
            "report_exists": report_exists,
            "failures": failures,
            "checks": checks,
        },
        list(dict.fromkeys(blockers)),
    )


def _local_marketplace_library_smoke_summary(vault: Path) -> tuple[dict[str, Any], list[str]]:
    result_relative_path, result_path = _local_marketplace_library_smoke_result_path(vault)
    payload = _read_json(result_path)
    blockers: list[str] = []
    if payload is None:
        return (
            {
                "result_path": result_relative_path.as_posix(),
                "result_exists": _is_file(result_path),
                "ok": False,
                "status": "missing_or_unreadable_local_marketplace_library_smoke",
                "elapsed_seconds": None,
                "failures": [],
                "checks": {},
                "flow_summary": {},
            },
            ["local_marketplace_library_smoke_missing_or_unreadable"],
        )

    checks = payload.get("checks") if isinstance(payload.get("checks"), dict) else {}
    failures = payload.get("failures") if isinstance(payload.get("failures"), list) else []
    flow_summary = payload.get("flow_summary") if isinstance(payload.get("flow_summary"), dict) else {}
    if payload.get("ok") is not True:
        blockers.append("local_marketplace_library_smoke_not_ok")
    if payload.get("status") != "COMPLETE / LOCAL MARKETPLACE LIBRARY STUDIO USE VERIFIED":
        blockers.append("local_marketplace_library_smoke_status_unexpected")
    if failures:
        blockers.append("local_marketplace_library_smoke_failures_present")
    for key in (
        "library_before_listed_not_installed",
        "library_after_ok",
        "library_after_has_one_item",
        "library_after_listed_installed",
        "library_item_installed",
        "library_item_registry_status_visible",
        "library_item_target_paths_verified",
        "panel_summary_library_ready",
        "panel_summary_library_read_only",
        "panel_registry_api_wired",
        "panel_registry_readiness_wired",
        "frontend_library_section_wired",
        "frontend_library_api_token_wired",
        "remote_exchange_blocked",
        "unauthorized_auto_install_blocked",
        "real_vault_registry_and_catalog_unchanged",
        "fixture_cleanup_completed",
    ):
        if checks.get(key) is not True:
            blockers.append(f"local_marketplace_library_smoke_check_failed:{key}")

    return (
        {
            "result_path": result_relative_path.as_posix(),
            "result_exists": _is_file(result_path),
            "ok": bool(payload.get("ok")),
            "status": payload.get("status") or "",
            "elapsed_seconds": payload.get("elapsed_seconds"),
            "failures": failures,
            "checks": checks,
            "flow_summary": flow_summary,
            "library_item_count": flow_summary.get("library_item_count"),
            "listed_installed_count": flow_summary.get("listed_installed_count"),
            "installed_unlisted_count": flow_summary.get("installed_unlisted_count"),
            "marketplace_install_executed": flow_summary.get("marketplace_install_executed"),
            "registry_written_in_fixture": flow_summary.get("registry_written_in_fixture"),
        },
        list(dict.fromkeys(blockers)),
    )


def _remote_distribution_smoke_summary(vault: Path) -> tuple[dict[str, Any], list[str]]:
    result_relative_path, result_path = _remote_distribution_smoke_result_path(vault)
    payload = _read_json(result_path)
    blockers: list[str] = []
    if payload is None:
        return (
            {
                "result_path": result_relative_path.as_posix(),
                "result_exists": _is_file(result_path),
                "ok": False,
                "status": "missing_or_unreadable_remote_distribution_smoke",
                "elapsed_seconds": None,
                "failures": [],
                "checks": {},
                "flow_summary": {},
            },
            ["remote_distribution_smoke_missing_or_unreadable"],
        )

    checks = payload.get("checks") if isinstance(payload.get("checks"), dict) else {}
    failures = payload.get("failures") if isinstance(payload.get("failures"), list) else []
    flow_summary = payload.get("flow_summary") if isinstance(payload.get("flow_summary"), dict) else {}
    if payload.get("ok") is not True:
        blockers.append("remote_distribution_smoke_not_ok")
    if payload.get("status") != "COMPLETE / GOVERNED REMOTE DISTRIBUTION FOUNDATION VERIFIED":
        blockers.append("remote_distribution_smoke_status_unexpected")
    if failures:
        blockers.append("remote_distribution_smoke_failures_present")
    for key in (
        "remote_preview_ready",
        "wrong_index_digest_blocked",
        "remote_index_written",
        "remote_network_publish_blocked",
        "remote_payment_mutation_blocked",
        "remote_license_checkout_blocked",
        "ingest_preview_trusted",
        "ingest_preview_attestation_verified",
        "wrong_ingest_statement_blocked",
        "remote_listing_ingested",
        "catalog_entry_written",
        "library_remote_item_visible",
        "library_item_not_installed",
        "panel_summary_remote_ready",
        "panel_summary_remote_ingest_ready",
        "panel_registry_remote_methods_wired",
        "panel_registry_remote_readiness_wired",
        "frontend_remote_section_wired",
        "frontend_remote_api_tokens_wired",
        "real_vault_registry_catalog_remote_index_unchanged",
        "fixture_cleanup_completed",
    ):
        if checks.get(key) is not True:
            blockers.append(f"remote_distribution_smoke_check_failed:{key}")

    return (
        {
            "result_path": result_relative_path.as_posix(),
            "result_exists": _is_file(result_path),
            "ok": bool(payload.get("ok")),
            "status": payload.get("status") or "",
            "elapsed_seconds": payload.get("elapsed_seconds"),
            "failures": failures,
            "checks": checks,
            "flow_summary": flow_summary,
            "remote_index_digest_sha256": flow_summary.get("remote_index_digest_sha256"),
            "listing_digest_sha256": flow_summary.get("listing_digest_sha256"),
            "ingested_listing_id": flow_summary.get("ingested_listing_id"),
            "catalog_entry_count": flow_summary.get("catalog_entry_count"),
            "library_item_count": flow_summary.get("library_item_count"),
        },
        list(dict.fromkeys(blockers)),
    )


def _hosted_marketplace_export_bundle_smoke_summary(vault: Path) -> tuple[dict[str, Any], list[str]]:
    result_relative_path, result_path = _hosted_marketplace_export_bundle_smoke_result_path(vault)
    payload = _read_json(result_path)
    blockers: list[str] = []
    if payload is None:
        return (
            {
                "result_path": result_relative_path.as_posix(),
                "result_exists": _is_file(result_path),
                "ok": False,
                "status": "missing_or_unreadable_hosted_marketplace_export_bundle_smoke",
                "elapsed_seconds": None,
                "failures": [],
                "checks": {},
                "flow_summary": {},
            },
            ["hosted_marketplace_export_bundle_smoke_missing_or_unreadable"],
        )

    checks = payload.get("checks") if isinstance(payload.get("checks"), dict) else {}
    failures = payload.get("failures") if isinstance(payload.get("failures"), list) else []
    flow_summary = payload.get("flow_summary") if isinstance(payload.get("flow_summary"), dict) else {}
    if payload.get("ok") is not True:
        blockers.append("hosted_marketplace_export_bundle_smoke_not_ok")
    if payload.get("status") != "COMPLETE / GOVERNED HOSTED MARKETPLACE EXPORT BUNDLE VERIFIED":
        blockers.append("hosted_marketplace_export_bundle_smoke_status_unexpected")
    if failures:
        blockers.append("hosted_marketplace_export_bundle_smoke_failures_present")
    for key in (
        "hosted_preview_ready",
        "wrong_bundle_digest_blocked",
        "wrong_remote_index_digest_blocked",
        "hosted_bundle_written",
        "manual_static_host_ready",
        "hosted_bundle_publication_manifest_ready",
        "hosted_bundle_no_credentials",
        "hosted_bundle_network_publish_blocked",
        "hosted_bundle_payment_mutation_blocked",
        "hosted_bundle_license_checkout_blocked",
        "hosted_bundle_package_install_blocked",
        "panel_summary_hosted_ready",
        "panel_summary_hosted_manual_static_ready",
        "panel_registry_hosted_methods_wired",
        "panel_registry_hosted_readiness_wired",
        "frontend_hosted_section_wired",
        "frontend_hosted_api_tokens_wired",
        "real_vault_registry_catalog_remote_index_hosted_bundle_unchanged",
        "fixture_cleanup_completed",
    ):
        if checks.get(key) is not True:
            blockers.append(f"hosted_marketplace_export_bundle_smoke_check_failed:{key}")

    return (
        {
            "result_path": result_relative_path.as_posix(),
            "result_exists": _is_file(result_path),
            "ok": bool(payload.get("ok")),
            "status": payload.get("status") or "",
            "elapsed_seconds": payload.get("elapsed_seconds"),
            "failures": failures,
            "checks": checks,
            "flow_summary": flow_summary,
            "remote_index_digest_sha256": flow_summary.get("remote_index_digest_sha256"),
            "hosted_bundle_digest_sha256": flow_summary.get("hosted_bundle_digest_sha256"),
            "hosted_bundle_artifact_path": flow_summary.get("hosted_bundle_artifact_path"),
            "entry_count": flow_summary.get("entry_count"),
            "publication_mode": flow_summary.get("publication_mode"),
        },
        list(dict.fromkeys(blockers)),
    )


def _static_host_publication_smoke_summary(vault: Path) -> tuple[dict[str, Any], list[str]]:
    result_relative_path, result_path = _static_host_publication_smoke_result_path(vault)
    payload = _read_json(result_path)
    blockers: list[str] = []
    if payload is None:
        return (
            {
                "result_path": result_relative_path.as_posix(),
                "result_exists": _is_file(result_path),
                "ok": False,
                "status": "missing_or_unreadable_static_host_publication_smoke",
                "elapsed_seconds": None,
                "failures": [],
                "checks": {},
                "flow_summary": {},
            },
            ["static_host_publication_smoke_missing_or_unreadable"],
        )

    checks = payload.get("checks") if isinstance(payload.get("checks"), dict) else {}
    failures = payload.get("failures") if isinstance(payload.get("failures"), list) else []
    flow_summary = payload.get("flow_summary") if isinstance(payload.get("flow_summary"), dict) else {}
    if payload.get("ok") is not True:
        blockers.append("static_host_publication_smoke_not_ok")
    if payload.get("status") != "COMPLETE / GOVERNED STATIC HOST PUBLICATION PROOF VERIFIED":
        blockers.append("static_host_publication_smoke_status_unexpected")
    if failures:
        blockers.append("static_host_publication_smoke_failures_present")
    for key in (
        "static_publication_preview_ready",
        "wrong_static_publication_digest_blocked",
        "wrong_hosted_bundle_digest_blocked",
        "wrong_remote_index_digest_blocked",
        "static_publication_written",
        "static_publication_files_ready",
        "manual_upload_ready",
        "network_upload_blocked",
        "external_registry_mutation_blocked",
        "payment_mutation_blocked",
        "license_checkout_blocked",
        "package_install_blocked",
        "panel_summary_static_ready",
        "panel_summary_static_manual_upload_ready",
        "panel_registry_static_methods_wired",
        "panel_registry_static_readiness_wired",
        "frontend_static_section_wired",
        "frontend_static_api_tokens_wired",
        "real_vault_registry_catalog_remote_index_hosted_bundle_static_publication_unchanged",
        "fixture_cleanup_completed",
    ):
        if checks.get(key) is not True:
            blockers.append(f"static_host_publication_smoke_check_failed:{key}")

    return (
        {
            "result_path": result_relative_path.as_posix(),
            "result_exists": _is_file(result_path),
            "ok": bool(payload.get("ok")),
            "status": payload.get("status") or "",
            "elapsed_seconds": payload.get("elapsed_seconds"),
            "failures": failures,
            "checks": checks,
            "flow_summary": flow_summary,
            "remote_index_digest_sha256": flow_summary.get("remote_index_digest_sha256"),
            "hosted_bundle_digest_sha256": flow_summary.get("hosted_bundle_digest_sha256"),
            "static_publication_digest_sha256": flow_summary.get("static_publication_digest_sha256"),
            "static_publication_dir_path": flow_summary.get("static_publication_dir_path"),
            "file_count": flow_summary.get("file_count"),
        },
        list(dict.fromkeys(blockers)),
    )


def _static_upload_handoff_smoke_summary(vault: Path) -> tuple[dict[str, Any], list[str]]:
    result_relative_path, result_path = _static_upload_handoff_smoke_result_path(vault)
    payload = _read_json(result_path)
    blockers: list[str] = []
    if payload is None:
        return (
            {
                "result_path": result_relative_path.as_posix(),
                "result_exists": _is_file(result_path),
                "ok": False,
                "status": "missing_or_unreadable_static_upload_handoff_smoke",
                "elapsed_seconds": None,
                "failures": [],
                "checks": {},
                "flow_summary": {},
            },
            ["static_upload_handoff_smoke_missing_or_unreadable"],
        )

    checks = payload.get("checks") if isinstance(payload.get("checks"), dict) else {}
    failures = payload.get("failures") if isinstance(payload.get("failures"), list) else []
    flow_summary = payload.get("flow_summary") if isinstance(payload.get("flow_summary"), dict) else {}
    if payload.get("ok") is not True:
        blockers.append("static_upload_handoff_smoke_not_ok")
    if payload.get("status") != "COMPLETE / GOVERNED STATIC HOST UPLOAD HANDOFF VERIFIED":
        blockers.append("static_upload_handoff_smoke_status_unexpected")
    if failures:
        blockers.append("static_upload_handoff_smoke_failures_present")
    for key in (
        "upload_handoff_preview_ready",
        "wrong_upload_handoff_digest_blocked",
        "wrong_static_publication_digest_blocked",
        "upload_handoff_written",
        "upload_handoff_files_written",
        "static_publication_files_present",
        "manual_upload_handoff_ready",
        "network_upload_blocked",
        "external_registry_mutation_blocked",
        "payment_mutation_blocked",
        "license_checkout_blocked",
        "package_install_blocked",
        "panel_summary_upload_handoff_ready",
        "panel_registry_upload_handoff_methods_wired",
        "panel_registry_upload_handoff_readiness_wired",
        "frontend_upload_handoff_section_wired",
        "frontend_upload_handoff_api_tokens_wired",
        "real_vault_registry_catalog_remote_index_hosted_bundle_static_publication_upload_handoff_unchanged",
        "fixture_cleanup_completed",
    ):
        if checks.get(key) is not True:
            blockers.append(f"static_upload_handoff_smoke_check_failed:{key}")

    return (
        {
            "result_path": result_relative_path.as_posix(),
            "result_exists": _is_file(result_path),
            "ok": bool(payload.get("ok")),
            "status": payload.get("status") or "",
            "elapsed_seconds": payload.get("elapsed_seconds"),
            "failures": failures,
            "checks": checks,
            "flow_summary": flow_summary,
            "remote_index_digest_sha256": flow_summary.get("remote_index_digest_sha256"),
            "hosted_bundle_digest_sha256": flow_summary.get("hosted_bundle_digest_sha256"),
            "static_publication_digest_sha256": flow_summary.get("static_publication_digest_sha256"),
            "upload_handoff_digest_sha256": flow_summary.get("upload_handoff_digest_sha256"),
            "upload_handoff_json_path": flow_summary.get("upload_handoff_json_path"),
            "upload_handoff_markdown_path": flow_summary.get("upload_handoff_markdown_path"),
            "file_count": flow_summary.get("file_count"),
        },
        list(dict.fromkeys(blockers)),
    )


def _static_upload_receipt_smoke_summary(vault: Path) -> tuple[dict[str, Any], list[str]]:
    result_relative_path, result_path = _static_upload_receipt_smoke_result_path(vault)
    payload = _read_json(result_path)
    blockers: list[str] = []
    if payload is None:
        return (
            {
                "result_path": result_relative_path.as_posix(),
                "result_exists": _is_file(result_path),
                "ok": False,
                "status": "missing_or_unreadable_static_upload_receipt_smoke",
                "elapsed_seconds": None,
                "failures": [],
                "checks": {},
                "flow_summary": {},
            },
            ["static_upload_receipt_smoke_missing_or_unreadable"],
        )

    checks = payload.get("checks") if isinstance(payload.get("checks"), dict) else {}
    failures = payload.get("failures") if isinstance(payload.get("failures"), list) else []
    flow_summary = payload.get("flow_summary") if isinstance(payload.get("flow_summary"), dict) else {}
    if payload.get("ok") is not True:
        blockers.append("static_upload_receipt_smoke_not_ok")
    if payload.get("status") != "COMPLETE / GOVERNED STATIC HOST UPLOAD RECEIPT VERIFIED":
        blockers.append("static_upload_receipt_smoke_status_unexpected")
    if failures:
        blockers.append("static_upload_receipt_smoke_failures_present")
    for key in (
        "upload_receipt_preview_ready",
        "wrong_upload_receipt_digest_blocked",
        "wrong_operator_receipt_statement_blocked",
        "wrong_upload_handoff_digest_blocked",
        "upload_receipt_written",
        "upload_receipt_files_written",
        "operator_receipt_statement_recorded",
        "operator_manual_upload_claim_recorded",
        "network_fetch_blocked",
        "network_upload_blocked",
        "external_registry_mutation_blocked",
        "payment_mutation_blocked",
        "license_checkout_blocked",
        "package_install_blocked",
        "panel_summary_upload_receipt_ready",
        "panel_registry_upload_receipt_methods_wired",
        "panel_registry_upload_receipt_readiness_wired",
        "frontend_upload_receipt_section_wired",
        "frontend_upload_receipt_api_tokens_wired",
        "real_vault_registry_catalog_remote_index_hosted_bundle_static_publication_upload_handoff_upload_receipt_unchanged",
        "fixture_cleanup_completed",
    ):
        if checks.get(key) is not True:
            blockers.append(f"static_upload_receipt_smoke_check_failed:{key}")

    return (
        {
            "result_path": result_relative_path.as_posix(),
            "result_exists": _is_file(result_path),
            "ok": bool(payload.get("ok")),
            "status": payload.get("status") or "",
            "elapsed_seconds": payload.get("elapsed_seconds"),
            "failures": failures,
            "checks": checks,
            "flow_summary": flow_summary,
            "remote_index_digest_sha256": flow_summary.get("remote_index_digest_sha256"),
            "hosted_bundle_digest_sha256": flow_summary.get("hosted_bundle_digest_sha256"),
            "static_publication_digest_sha256": flow_summary.get("static_publication_digest_sha256"),
            "upload_handoff_digest_sha256": flow_summary.get("upload_handoff_digest_sha256"),
            "upload_receipt_digest_sha256": flow_summary.get("upload_receipt_digest_sha256"),
            "upload_receipt_json_path": flow_summary.get("upload_receipt_json_path"),
            "upload_receipt_markdown_path": flow_summary.get("upload_receipt_markdown_path"),
            "operator_uploaded_base_url": flow_summary.get("operator_uploaded_base_url"),
            "file_count": flow_summary.get("file_count"),
        },
        list(dict.fromkeys(blockers)),
    )


def _published_static_index_registration_smoke_summary(vault: Path) -> tuple[dict[str, Any], list[str]]:
    result_relative_path, result_path = _published_static_index_registration_smoke_result_path(vault)
    payload = _read_json(result_path)
    blockers: list[str] = []
    if payload is None:
        return (
            {
                "result_path": result_relative_path.as_posix(),
                "result_exists": _is_file(result_path),
                "ok": False,
                "status": "missing_or_unreadable_published_static_index_registration_smoke",
                "elapsed_seconds": None,
                "failures": [],
                "checks": {},
                "flow_summary": {},
            },
            ["published_static_index_registration_smoke_missing_or_unreadable"],
        )

    checks = payload.get("checks") if isinstance(payload.get("checks"), dict) else {}
    failures = payload.get("failures") if isinstance(payload.get("failures"), list) else []
    flow_summary = payload.get("flow_summary") if isinstance(payload.get("flow_summary"), dict) else {}
    if payload.get("ok") is not True:
        blockers.append("published_static_index_registration_smoke_not_ok")
    if payload.get("status") != "COMPLETE / GOVERNED PUBLISHED STATIC INDEX REGISTRATION VERIFIED":
        blockers.append("published_static_index_registration_smoke_status_unexpected")
    if failures:
        blockers.append("published_static_index_registration_smoke_failures_present")
    for key in (
        "published_static_index_registration_preview_ready",
        "wrong_published_static_index_registration_digest_blocked",
        "wrong_operator_registration_statement_blocked",
        "wrong_upload_receipt_digest_blocked",
        "published_static_index_registration_written",
        "published_static_index_registration_files_written",
        "operator_registration_statement_recorded",
        "operator_declared_published_index_registered",
        "live_url_fetch_unverified_and_blocked",
        "network_upload_blocked",
        "external_registry_mutation_blocked",
        "payment_mutation_blocked",
        "license_checkout_blocked",
        "package_install_blocked",
        "panel_summary_published_static_index_registration_ready",
        "panel_registry_published_static_index_registration_methods_wired",
        "panel_registry_published_static_index_registration_readiness_wired",
        "frontend_published_static_index_registration_section_wired",
        "frontend_published_static_index_registration_api_tokens_wired",
        "real_vault_registry_catalog_distribution_registration_paths_unchanged",
        "fixture_cleanup_completed",
    ):
        if checks.get(key) is not True:
            blockers.append(f"published_static_index_registration_smoke_check_failed:{key}")

    return (
        {
            "result_path": result_relative_path.as_posix(),
            "result_exists": _is_file(result_path),
            "ok": bool(payload.get("ok")),
            "status": payload.get("status") or "",
            "elapsed_seconds": payload.get("elapsed_seconds"),
            "failures": failures,
            "checks": checks,
            "flow_summary": flow_summary,
            "remote_index_digest_sha256": flow_summary.get("remote_index_digest_sha256"),
            "hosted_bundle_digest_sha256": flow_summary.get("hosted_bundle_digest_sha256"),
            "static_publication_digest_sha256": flow_summary.get("static_publication_digest_sha256"),
            "upload_handoff_digest_sha256": flow_summary.get("upload_handoff_digest_sha256"),
            "upload_receipt_digest_sha256": flow_summary.get("upload_receipt_digest_sha256"),
            "published_static_index_registration_digest_sha256": flow_summary.get(
                "published_static_index_registration_digest_sha256"
            ),
            "published_static_index_registration_json_path": flow_summary.get(
                "published_static_index_registration_json_path"
            ),
            "published_static_index_registration_markdown_path": flow_summary.get(
                "published_static_index_registration_markdown_path"
            ),
            "operator_published_static_index_url": flow_summary.get("operator_published_static_index_url"),
            "file_count": flow_summary.get("file_count"),
        },
        list(dict.fromkeys(blockers)),
    )


def _authority(write: bool, written: bool) -> dict[str, Any]:
    authority = {flag: False for flag in FORBIDDEN_AUTHORITY_FLAGS}
    authority.update(
        {
            "proof_deck_log_artifact_write_allowed": bool(write),
            "proof_deck_log_artifact_written": bool(written),
            "log_only": True,
        }
    )
    return authority


def _validate_authority(authority: dict[str, Any]) -> list[str]:
    return [flag for flag in FORBIDDEN_AUTHORITY_FLAGS if authority.get(flag) is not False]


def _deck_paths(vault: Path, slug: str) -> tuple[Path, Path]:
    root = (vault / OUTPUT_ROOT).resolve()
    safe = _safe_slug(slug)
    markdown_path = root / f"{safe}.md"
    json_path = root / f"{safe}.json"
    _assert_inside(markdown_path, root)
    _assert_inside(json_path, root)
    return markdown_path, json_path


def _build_slides(
    *,
    evidence: list[dict[str, Any]],
    visual: dict[str, Any],
    studio_clickthrough: dict[str, Any],
    marketplace_bridge: dict[str, Any],
    live_studio_control: dict[str, Any],
    operator_use: dict[str, Any],
    operator_use_closeout_smoke: dict[str, Any],
    local_marketplace_library_smoke: dict[str, Any],
    remote_distribution_smoke: dict[str, Any],
    hosted_marketplace_export_bundle_smoke: dict[str, Any],
    static_host_publication_smoke: dict[str, Any],
    static_upload_handoff_smoke: dict[str, Any],
    static_upload_receipt_smoke: dict[str, Any],
    published_static_index_registration_smoke: dict[str, Any],
    blockers: list[str],
) -> list[dict[str, Any]]:
    build_paths = [item["path"] for item in evidence if item["kind"] == "build_log"]
    doc_paths = [item["path"] for item in evidence if item["kind"] == "doc"]
    visual_refs = [visual["report_path"], *[shot["path"] for shot in visual.get("screenshots") or []]]
    clickthrough_refs = [
        studio_clickthrough["report_path"],
        *[shot["path"] for shot in studio_clickthrough.get("screenshots") or []],
    ]
    marketplace_bridge_refs = [
        marketplace_bridge["report_path"],
        *[shot["path"] for shot in marketplace_bridge.get("screenshots") or []],
    ]
    live_control_refs = [live_studio_control["report_path"]]
    operator_use_refs = [
        operator_use["report_path"],
        *[shot["path"] for shot in operator_use.get("screenshots") or []],
        operator_use_closeout_smoke.get("result_path") or "",
    ]
    local_marketplace_library_refs = [local_marketplace_library_smoke.get("result_path") or ""]
    remote_distribution_refs = [remote_distribution_smoke.get("result_path") or ""]
    hosted_bundle_refs = [hosted_marketplace_export_bundle_smoke.get("result_path") or ""]
    static_publication_refs = [static_host_publication_smoke.get("result_path") or ""]
    static_upload_handoff_refs = [static_upload_handoff_smoke.get("result_path") or ""]
    static_upload_receipt_refs = [static_upload_receipt_smoke.get("result_path") or ""]
    published_static_index_registration_refs = [
        published_static_index_registration_smoke.get("result_path") or ""
    ]
    return [
        {
            "id": "scope",
            "title": "Chaser Forge Proof Scope",
            "status": "COMPLETE" if not blockers else "PARTIAL",
            "bullets": [
                "Packages existing Forge implementation, Approval Center routing, lifecycle visual QA, Studio proof-deck clickthrough, marketplace bridge visual evidence, live StudioAPI control proof, operator-use Studio button proof, Local Marketplace Library smoke evidence, Remote Distribution smoke evidence, Hosted Export Bundle smoke evidence, Static Host Publication smoke evidence, Static Upload Handoff smoke evidence, Static Upload Receipt smoke evidence, and Published Static Index Registration smoke evidence.",
                "Closes the governed Chaser Forge evidence chain including local public catalog publish, read-only Studio marketplace library inspection, digest-bound remote index/listing ingest, manual static-host export bundles, digest-bound upload-ready static files, manual upload handoff artifacts, local post-upload receipt artifacts, local published index registration artifacts, and approved marketplace package install.",
                "Writes only Markdown/JSON proof artifacts when write mode is explicit.",
            ],
            "evidence_refs": doc_paths,
        },
        {
            "id": "lifecycle-chain",
            "title": "Lifecycle Chain Evidence",
            "status": "VERIFIED" if all(item["exists"] for item in evidence if item["kind"] == "build_log") else "PARTIAL",
            "bullets": [
                "MVP foundation, registry, sandbox approval, sandbox writer, live approval, live executor, rollback executor, Approval Center routing, UI lifecycle proof, marketplace completion, and operator-use closeout each have dated build-log evidence.",
                "Sandbox writes are extension-owned only; live and rollback executors mutate registry lifecycle metadata only.",
                "Rollback retains extension files and preserves prior live execution history.",
            ],
            "evidence_refs": build_paths,
        },
        {
            "id": "approval-center-visibility",
            "title": "Approval Center Visibility",
            "status": "VERIFIED" if visual.get("ok") and not blockers else "PARTIAL",
            "bullets": [
                "Forge approval artifacts route into the read-only Approval Center source group.",
                "Rendered lifecycle states include pending, approved-pending-execution, consumed, rejected, and invalid.",
                "Desktop and mobile screenshots were captured from the production frontend renderer.",
            ],
            "evidence_refs": visual_refs,
        },
        {
            "id": "studio-clickthrough",
            "title": "Studio Proof Deck Clickthrough",
            "status": "VERIFIED" if studio_clickthrough.get("ok") and not blockers else "PARTIAL",
            "bullets": [
                "The native Studio Chaser Forge panel renders a read-only Proof Deck section.",
                "The section displays proof-deck status, Markdown/JSON artifact paths, slide statuses, and next-pass posture.",
                "Desktop and mobile screenshots were captured from the production Studio shell route.",
            ],
            "evidence_refs": clickthrough_refs,
        },
        {
            "id": "marketplace-bridge-handoff",
            "title": "Marketplace Publish And Install",
            "status": "VERIFIED" if marketplace_bridge.get("ok") and not blockers else "PARTIAL",
            "bullets": [
                "The Marketplace Publish And Install panel surface renders catalog, publish, import review, sandbox request, and install executor state.",
                "The visual QA proof shows sandbox request preview/write APIs plus the `forge_marketplace_import_sandbox_request_written` state.",
                "The bridge proof preserves no package install, while the live StudioAPI proof verifies the later approved install executor path.",
            ],
            "evidence_refs": marketplace_bridge_refs,
        },
        {
            "id": "live-studio-control-proof",
            "title": "Live Studio Control Proof",
            "status": "VERIFIED" if live_studio_control.get("ok") and not blockers else "PARTIAL",
            "bullets": [
                "StudioAPI controls drive sandbox approval/decision/execution, live approval/decision/execution, and rollback approval/decision/execution in temporary fixtures.",
                "Marketplace controls drive catalog publish, import review approval, sandbox approval, marketplace install execution, approval consumption, registry/file writes, and exact-once marker reservation in temporary fixtures.",
                "The proof confirms duplicate marketplace install is blocked after the import approval is consumed.",
            ],
            "evidence_refs": live_control_refs,
        },
        {
            "id": "operator-use-studio-proof",
            "title": "Operator Use Studio Button Proof",
            "status": "VERIFIED" if operator_use.get("ok") and not blockers else "PARTIAL",
            "bullets": [
                "The production Studio shell route was rendered and the actual Publish Demo Package and Run Demo Marketplace Install controls were clicked.",
                "The proof verifies visible final status after panel refresh for both publish and install, including the previously fragile status element replacement path.",
                "The button flow exercised required StudioAPI marketplace methods, accepted two test confirmations, and wrote registry/files/exact-once marker only inside a temporary fixture vault.",
                "The direct closeout smoke replaces the hanging pytest wrapper with `python -u`, faulthandler timeout, explicit JSON output, and deterministic fixture cleanup.",
            ],
            "evidence_refs": [ref for ref in operator_use_refs if ref],
        },
        {
            "id": "local-marketplace-library",
            "title": "Local Marketplace Library",
            "status": "VERIFIED" if local_marketplace_library_smoke.get("ok") and not blockers else "PARTIAL",
            "bullets": [
                "The Studio panel exposes a read-only Local Marketplace Library that joins the local catalog and Forge extension registry.",
                "The direct smoke drives catalog publish, approved marketplace install, and library refresh without pytest or Playwright.",
                "The smoke verifies listed-not-installed to listed-installed state, registry status, target path evidence, panel registry API wiring, frontend section tokens, and fixture cleanup.",
                "Remote exchange and unauthorized auto-install remain blocked, and the real vault registry/catalog are verified unchanged.",
            ],
            "evidence_refs": [ref for ref in local_marketplace_library_refs if ref],
        },
        {
            "id": "remote-distribution-foundation",
            "title": "Remote Distribution Foundation",
            "status": "VERIFIED" if remote_distribution_smoke.get("ok") and not blockers else "PARTIAL",
            "bullets": [
                "The Studio panel exposes Remote Distribution controls for digest-gated remote index writing and verified remote listing ingest.",
                "The direct smoke writes the remote index and ingests the listing inside a fixture vault without pytest, Playwright, network calls, or payment mutation.",
                "The smoke verifies publisher trust, attestation, exact digest gates, exact operator confirmation, local catalog ingest, Local Marketplace Library visibility, frontend tokens, panel registry readiness, and fixture cleanup.",
                "Real-vault registry, catalog, and remote-index paths are verified unchanged.",
            ],
            "evidence_refs": [ref for ref in remote_distribution_refs if ref],
        },
        {
            "id": "hosted-marketplace-export-bundle",
            "title": "Hosted Marketplace Export Bundle",
            "status": "VERIFIED" if hosted_marketplace_export_bundle_smoke.get("ok") and not blockers else "PARTIAL",
            "bullets": [
                "The Studio panel exposes a Hosted Export Bundle control for digest-gated manual static-host marketplace bundle artifacts.",
                "The direct smoke writes the hosted bundle inside a fixture vault without pytest, Playwright, network publication, credentials, payment mutation, license checkout, or package installation.",
                "The smoke verifies exact hosted-bundle and remote-index digest gates, publication manifest shape, frontend tokens, panel registry readiness, and fixture cleanup.",
                "Real-vault registry, catalog, remote-index, and hosted-bundle paths are verified unchanged.",
            ],
            "evidence_refs": [ref for ref in hosted_bundle_refs if ref],
        },
        {
            "id": "static-host-publication-proof",
            "title": "Static Host Publication Proof",
            "status": "VERIFIED" if static_host_publication_smoke.get("ok") and not blockers else "PARTIAL",
            "bullets": [
                "The Studio panel exposes a Static Publication control for digest-gated upload-ready static-host proof directories.",
                "The direct smoke writes index.json, README.md, hosted-bundle.json, publication-manifest.json, and checksums.json inside a fixture vault without network upload, external registry mutation, payment mutation, license checkout, or package installation.",
                "The smoke verifies exact remote-index, hosted-bundle, and static-publication digest gates, frontend tokens, panel registry readiness, and fixture cleanup.",
                "Real-vault registry, catalog, remote-index, hosted-bundle, and static-publication paths are verified unchanged.",
            ],
            "evidence_refs": [ref for ref in static_publication_refs if ref],
        },
        {
            "id": "static-upload-handoff",
            "title": "Static Upload Handoff",
            "status": "VERIFIED" if static_upload_handoff_smoke.get("ok") and not blockers else "PARTIAL",
            "bullets": [
                "The Studio panel exposes an Upload Handoff control for digest-gated local operator upload handoff artifacts.",
                "The direct smoke writes JSON and Markdown handoff artifacts inside a fixture vault after verifying the static publication files are present and digest-matched.",
                "The smoke verifies upload-handoff and static-publication digest gates, frontend tokens, panel registry readiness, and fixture cleanup.",
                "Real-vault registry, catalog, remote-index, hosted-bundle, static-publication, and upload-handoff paths are verified unchanged.",
            ],
            "evidence_refs": [ref for ref in static_upload_handoff_refs if ref],
        },
        {
            "id": "static-upload-receipt",
            "title": "Static Upload Receipt",
            "status": "VERIFIED" if static_upload_receipt_smoke.get("ok") and not blockers else "PARTIAL",
            "bullets": [
                "The Studio panel exposes an Upload Receipt control for digest-gated local operator receipt artifacts after manual static-host upload.",
                "The direct smoke writes JSON and Markdown receipt artifacts inside a fixture vault with exact source digest gates and exact operator receipt statement.",
                "The smoke verifies upload-receipt and upload-handoff digest gates, frontend tokens, panel registry readiness, network fetch blocked posture, and fixture cleanup.",
                "Real-vault registry, catalog, remote-index, hosted-bundle, static-publication, upload-handoff, and upload-receipt paths are verified unchanged.",
            ],
            "evidence_refs": [ref for ref in static_upload_receipt_refs if ref],
        },
        {
            "id": "published-static-index-registration",
            "title": "Published Static Index Registration",
            "status": "VERIFIED" if published_static_index_registration_smoke.get("ok") and not blockers else "PARTIAL",
            "bullets": [
                "The Studio panel exposes a Register Published Index control for digest-gated local registration artifacts after upload receipt.",
                "The direct smoke writes JSON and Markdown registration artifacts inside a fixture vault with exact source digest gates and exact operator registration statement.",
                "The smoke verifies registration and upload-receipt digest gates, frontend tokens, panel registry readiness, live URL fetch blocked posture, and fixture cleanup.",
                "Real-vault registry, catalog, remote-index, hosted-bundle, static-publication, upload-handoff, upload-receipt, and registration paths are verified unchanged.",
            ],
            "evidence_refs": [ref for ref in published_static_index_registration_refs if ref],
        },
        {
            "id": "authority-boundary",
            "title": "Authority Boundary",
            "status": "PRESERVED",
            "bullets": [
                "No approval decision writer is added.",
                "No approval consumption or Forge executor is run by the proof deck.",
                "No provider/model call, schedule activation, Agent Bus dispatch, secret read, protected-core write, Pulse memory, Personal Map, R&D truth-state, or canonical mutation is allowed.",
            ],
            "evidence_refs": doc_paths,
        },
        {
            "id": "external-boundaries",
            "title": "External Boundaries",
            "status": "BLOCKED BY DESIGN",
            "bullets": [
                "Ambient remote third-party marketplace calls remain blocked; the implemented remote lane is a digest-bound index artifact, verified local-catalog ingest foundation, manual static-host export bundle, local static-host publication proof directory, local upload handoff, local upload receipt, and local published static index registration.",
                "Payment and license checkout mutation remain blocked.",
                "Generic Approval Center write controls remain blocked; Forge decision writes stay source-specific.",
                "Provider/model calls, Agent Bus dispatch, protected-core mutation, memory mutation, R&D truth-state mutation, and canonical mutation remain blocked.",
            ],
            "evidence_refs": [],
        },
    ]


def render_chaser_forge_proof_deck_markdown(deck: dict[str, Any]) -> str:
    """Render the proof deck as a compact Markdown evidence artifact."""

    evidence_rows = []
    for item in deck.get("evidence_matrix") or []:
        marker = "present" if item.get("exists") else "missing"
        evidence_rows.append(
            f"| {item.get('kind', '')} | {marker} | `{item.get('path', '')}` | {item.get('status_hint') or item.get('summary', '')} |"
        )
    if not evidence_rows:
        evidence_rows.append("| none | missing |  |  |")

    visual = deck.get("visual_qa") or {}
    studio_clickthrough = deck.get("studio_clickthrough") or {}
    marketplace_bridge = deck.get("marketplace_bridge_visual_qa") or {}
    live_studio_control = deck.get("live_studio_control_proof") or {}
    operator_use = deck.get("operator_use_studio_proof") or {}
    operator_use_closeout_smoke = deck.get("operator_use_closeout_smoke") or {}
    local_marketplace_library_smoke = deck.get("local_marketplace_library_smoke") or {}
    remote_distribution_smoke = deck.get("remote_distribution_smoke") or {}
    hosted_marketplace_export_bundle_smoke = deck.get("hosted_marketplace_export_bundle_smoke") or {}
    static_host_publication_smoke = deck.get("static_host_publication_smoke") or {}
    static_upload_handoff_smoke = deck.get("static_upload_handoff_smoke") or {}
    static_upload_receipt_smoke = deck.get("static_upload_receipt_smoke") or {}
    published_static_index_registration_smoke = deck.get("published_static_index_registration_smoke") or {}
    screenshots = "\n".join(
        f"- {shot.get('viewport')}: `{shot.get('path')}` exists={str(bool(shot.get('exists'))).lower()} bytes={shot.get('bytes')}"
        for shot in visual.get("screenshots") or []
    ) or "- None"
    clickthrough_screenshots = "\n".join(
        f"- {shot.get('viewport')}: `{shot.get('path')}` exists={str(bool(shot.get('exists'))).lower()} bytes={shot.get('bytes')} proof_deck_section_visible={str(bool(shot.get('proof_deck_section_visible'))).lower()}"
        for shot in studio_clickthrough.get("screenshots") or []
    ) or "- None"
    marketplace_bridge_screenshots = "\n".join(
        f"- {shot.get('viewport')}: `{shot.get('path')}` exists={str(bool(shot.get('exists'))).lower()} bytes={shot.get('bytes')} bridge_written_state_visible={str(bool(shot.get('bridge_written_state_visible'))).lower()}"
        for shot in marketplace_bridge.get("screenshots") or []
    ) or "- None"
    operator_use_screenshots = "\n".join(
        f"- {shot.get('step')} / {shot.get('viewport')}: `{shot.get('path')}` exists={str(bool(shot.get('exists'))).lower()} bytes={shot.get('bytes')} status={shot.get('status_state')} text={shot.get('status_text')}"
        for shot in operator_use.get("screenshots") or []
    ) or "- None"
    slides = []
    for slide in deck.get("slides") or []:
        bullets = "\n".join(f"- {bullet}" for bullet in slide.get("bullets") or [])
        refs = "\n".join(f"- `{ref}`" for ref in slide.get("evidence_refs") or []) or "- None"
        slides.append(
            "\n".join(
                [
                    f"## {slide.get('title')}",
                    "",
                    f"Status: {slide.get('status')}",
                    "",
                    bullets,
                    "",
                    "Evidence refs:",
                    refs,
                    "",
                ]
            )
        )

    authority = deck.get("authority") or {}
    blocked_flags = [flag for flag in FORBIDDEN_AUTHORITY_FLAGS if authority.get(flag) is False]
    return "\n".join(
        [
            "# Chaser Forge Proof Deck",
            "",
            f"- Date: {deck.get('date')}",
            f"- Runtime: {deck.get('runtime')}",
            f"- Session descriptor: `{deck.get('session_descriptor')}`",
            f"- Status: {deck.get('status')}",
            f"- Feature status: {deck.get('feature_status')}",
            f"- Deck artifact role: {deck.get('artifact_role')}",
            "",
            "## Evidence Matrix",
            "",
            "| Kind | State | Path | Status / Summary |",
            "|---|---|---|---|",
            *evidence_rows,
            "",
            "## Visual QA Summary",
            "",
            f"- Report ok: {str(bool(visual.get('ok'))).lower()}",
            f"- Lifecycle statuses: {', '.join(visual.get('lifecycle_statuses') or [])}",
            f"- Status counts: `{json.dumps(visual.get('status_counts') or {}, sort_keys=True)}`",
            f"- Fixture vault persisted: {str(visual.get('fixture_vault_persisted')).lower()}",
            "",
            "Screenshots:",
            screenshots,
            "",
            "## Studio Clickthrough Summary",
            "",
            f"- Report ok: {str(bool(studio_clickthrough.get('ok'))).lower()}",
            f"- Proof deck section visible: {str(bool(studio_clickthrough.get('proof_deck_section_visible'))).lower()}",
            f"- Missing required tokens: `{json.dumps(studio_clickthrough.get('missing_required_tokens') or [])}`",
            "",
            "Screenshots:",
            clickthrough_screenshots,
            "",
            "## Marketplace Bridge Visual QA Summary",
            "",
            f"- Report ok: {str(bool(marketplace_bridge.get('ok'))).lower()}",
            f"- Marketplace section visible: {str(bool(marketplace_bridge.get('marketplace_section_visible'))).lower()}",
            f"- Bridge APIs visible: {str(bool(marketplace_bridge.get('bridge_api_tokens_visible'))).lower()}",
            f"- Bridge written state visible: {str(bool(marketplace_bridge.get('bridge_written_state_visible'))).lower()}",
            f"- Sandbox request written: {str(bool(marketplace_bridge.get('sandbox_approval_request_written'))).lower()}",
            f"- Marketplace import approval consumed: {str(marketplace_bridge.get('marketplace_import_approval_consumed')).lower()}",
            f"- Sandbox approval consumed: {str(marketplace_bridge.get('sandbox_approval_consumed')).lower()}",
            f"- Registry written: {str(marketplace_bridge.get('registry_written')).lower()}",
            f"- Exact-once marker reserved: {str(marketplace_bridge.get('exact_once_marker_reserved')).lower()}",
            f"- Sandbox approval artifact: `{marketplace_bridge.get('sandbox_approval_artifact_path') or ''}`",
            "",
            "Screenshots:",
            marketplace_bridge_screenshots,
            "",
            "## Live Studio Control Proof Summary",
            "",
            f"- Report ok: {str(bool(live_studio_control.get('ok'))).lower()}",
            f"- Sandbox registry written: {str(live_studio_control.get('sandbox_registry_written')).lower()}",
            f"- Live install executed: {str(live_studio_control.get('live_install_executed')).lower()}",
            f"- Rollback executed: {str(live_studio_control.get('rollback_executed')).lower()}",
            f"- Registry returned to sandbox: {str(live_studio_control.get('registry_returned_to_sandbox')).lower()}",
            f"- Package artifact written: {str(live_studio_control.get('package_artifact_written')).lower()}",
            f"- Catalog listing written: {str(live_studio_control.get('catalog_listing_written')).lower()}",
            f"- Import approval written: {str(live_studio_control.get('import_approval_written')).lower()}",
            f"- Sandbox request written: {str(live_studio_control.get('sandbox_request_written')).lower()}",
            f"- Marketplace import approval consumed: {str(live_studio_control.get('marketplace_import_approval_consumed')).lower()}",
            f"- Marketplace install executed: {str(live_studio_control.get('marketplace_install_executed')).lower()}",
            f"- Marketplace install registry written: {str(live_studio_control.get('marketplace_install_registry_written')).lower()}",
            f"- Marketplace install exact-once marker reserved: {str(live_studio_control.get('marketplace_install_exact_once_marker_reserved')).lower()}",
            f"- Fixture cleanup completed: {str(live_studio_control.get('fixture_cleanup_completed')).lower()}",
            f"- Report path: `{live_studio_control.get('report_path') or ''}`",
            "",
            "## Operator Use Studio Proof Summary",
            "",
            f"- Report ok: {str(bool(operator_use.get('ok'))).lower()}",
            f"- Publish status visible after refresh: {str(operator_use.get('publish_status_visible_after_refresh')).lower()}",
            f"- Install status visible after refresh: {str(operator_use.get('install_status_visible_after_refresh')).lower()}",
            f"- Required API methods called: {str(operator_use.get('required_api_methods_called')).lower()}",
            f"- Operator confirmations accepted: {operator_use.get('operator_confirmations_accepted')}",
            f"- Fixture registry written: {str(operator_use.get('fixture_registry_written')).lower()}",
            f"- Fixture extension files written: {str(operator_use.get('fixture_extension_files_written')).lower()}",
            f"- Fixture exact-once marker written: {str(operator_use.get('fixture_exact_once_marker_written')).lower()}",
            f"- Report path: `{operator_use.get('report_path') or ''}`",
            "",
            "Screenshots:",
            operator_use_screenshots,
            "",
            "## Operator Use Closeout Smoke Summary",
            "",
            f"- Result ok: {str(bool(operator_use_closeout_smoke.get('ok'))).lower()}",
            f"- Status: {operator_use_closeout_smoke.get('status') or ''}",
            f"- Elapsed seconds: {operator_use_closeout_smoke.get('elapsed_seconds')}",
            f"- Result path: `{operator_use_closeout_smoke.get('result_path') or ''}`",
            f"- Report path: `{operator_use_closeout_smoke.get('report_path') or ''}`",
            f"- Failures: `{json.dumps(operator_use_closeout_smoke.get('failures') or [])}`",
            "",
            "## Local Marketplace Library Smoke Summary",
            "",
            f"- Result ok: {str(bool(local_marketplace_library_smoke.get('ok'))).lower()}",
            f"- Status: {local_marketplace_library_smoke.get('status') or ''}",
            f"- Elapsed seconds: {local_marketplace_library_smoke.get('elapsed_seconds')}",
            f"- Result path: `{local_marketplace_library_smoke.get('result_path') or ''}`",
            f"- Library item count: {local_marketplace_library_smoke.get('library_item_count')}",
            f"- Listed installed count: {local_marketplace_library_smoke.get('listed_installed_count')}",
            f"- Marketplace install executed: {str(local_marketplace_library_smoke.get('marketplace_install_executed')).lower()}",
            f"- Registry written in fixture: {str(local_marketplace_library_smoke.get('registry_written_in_fixture')).lower()}",
            f"- Failures: `{json.dumps(local_marketplace_library_smoke.get('failures') or [])}`",
            "",
            "## Remote Distribution Smoke Summary",
            "",
            f"- Result ok: {str(bool(remote_distribution_smoke.get('ok'))).lower()}",
            f"- Status: {remote_distribution_smoke.get('status') or ''}",
            f"- Elapsed seconds: {remote_distribution_smoke.get('elapsed_seconds')}",
            f"- Result path: `{remote_distribution_smoke.get('result_path') or ''}`",
            f"- Remote index digest: `{remote_distribution_smoke.get('remote_index_digest_sha256') or ''}`",
            f"- Listing digest: `{remote_distribution_smoke.get('listing_digest_sha256') or ''}`",
            f"- Ingested listing id: `{remote_distribution_smoke.get('ingested_listing_id') or ''}`",
            f"- Catalog entry count: {remote_distribution_smoke.get('catalog_entry_count')}",
            f"- Library item count: {remote_distribution_smoke.get('library_item_count')}",
            f"- Failures: `{json.dumps(remote_distribution_smoke.get('failures') or [])}`",
            "",
            "## Hosted Marketplace Export Bundle Smoke Summary",
            "",
            f"- Result ok: {str(bool(hosted_marketplace_export_bundle_smoke.get('ok'))).lower()}",
            f"- Status: {hosted_marketplace_export_bundle_smoke.get('status') or ''}",
            f"- Elapsed seconds: {hosted_marketplace_export_bundle_smoke.get('elapsed_seconds')}",
            f"- Result path: `{hosted_marketplace_export_bundle_smoke.get('result_path') or ''}`",
            f"- Remote index digest: `{hosted_marketplace_export_bundle_smoke.get('remote_index_digest_sha256') or ''}`",
            f"- Hosted bundle digest: `{hosted_marketplace_export_bundle_smoke.get('hosted_bundle_digest_sha256') or ''}`",
            f"- Hosted bundle artifact path: `{hosted_marketplace_export_bundle_smoke.get('hosted_bundle_artifact_path') or ''}`",
            f"- Entry count: {hosted_marketplace_export_bundle_smoke.get('entry_count')}",
            f"- Publication mode: `{hosted_marketplace_export_bundle_smoke.get('publication_mode') or ''}`",
            f"- Failures: `{json.dumps(hosted_marketplace_export_bundle_smoke.get('failures') or [])}`",
            "",
            "## Static Host Publication Smoke Summary",
            "",
            f"- Result ok: {str(bool(static_host_publication_smoke.get('ok'))).lower()}",
            f"- Status: {static_host_publication_smoke.get('status') or ''}",
            f"- Elapsed seconds: {static_host_publication_smoke.get('elapsed_seconds')}",
            f"- Result path: `{static_host_publication_smoke.get('result_path') or ''}`",
            f"- Remote index digest: `{static_host_publication_smoke.get('remote_index_digest_sha256') or ''}`",
            f"- Hosted bundle digest: `{static_host_publication_smoke.get('hosted_bundle_digest_sha256') or ''}`",
            f"- Static publication digest: `{static_host_publication_smoke.get('static_publication_digest_sha256') or ''}`",
            f"- Static publication directory: `{static_host_publication_smoke.get('static_publication_dir_path') or ''}`",
            f"- File count: {static_host_publication_smoke.get('file_count')}",
            f"- Failures: `{json.dumps(static_host_publication_smoke.get('failures') or [])}`",
            "",
            "## Static Upload Handoff Smoke Summary",
            "",
            f"- Result ok: {str(bool(static_upload_handoff_smoke.get('ok'))).lower()}",
            f"- Status: {static_upload_handoff_smoke.get('status') or ''}",
            f"- Elapsed seconds: {static_upload_handoff_smoke.get('elapsed_seconds')}",
            f"- Result path: `{static_upload_handoff_smoke.get('result_path') or ''}`",
            f"- Remote index digest: `{static_upload_handoff_smoke.get('remote_index_digest_sha256') or ''}`",
            f"- Hosted bundle digest: `{static_upload_handoff_smoke.get('hosted_bundle_digest_sha256') or ''}`",
            f"- Static publication digest: `{static_upload_handoff_smoke.get('static_publication_digest_sha256') or ''}`",
            f"- Upload handoff digest: `{static_upload_handoff_smoke.get('upload_handoff_digest_sha256') or ''}`",
            f"- Upload handoff JSON: `{static_upload_handoff_smoke.get('upload_handoff_json_path') or ''}`",
            f"- Upload handoff Markdown: `{static_upload_handoff_smoke.get('upload_handoff_markdown_path') or ''}`",
            f"- File count: {static_upload_handoff_smoke.get('file_count')}",
            f"- Failures: `{json.dumps(static_upload_handoff_smoke.get('failures') or [])}`",
            "",
            "## Static Upload Receipt Smoke Summary",
            "",
            f"- Result ok: {str(bool(static_upload_receipt_smoke.get('ok'))).lower()}",
            f"- Status: {static_upload_receipt_smoke.get('status') or ''}",
            f"- Elapsed seconds: {static_upload_receipt_smoke.get('elapsed_seconds')}",
            f"- Result path: `{static_upload_receipt_smoke.get('result_path') or ''}`",
            f"- Remote index digest: `{static_upload_receipt_smoke.get('remote_index_digest_sha256') or ''}`",
            f"- Hosted bundle digest: `{static_upload_receipt_smoke.get('hosted_bundle_digest_sha256') or ''}`",
            f"- Static publication digest: `{static_upload_receipt_smoke.get('static_publication_digest_sha256') or ''}`",
            f"- Upload handoff digest: `{static_upload_receipt_smoke.get('upload_handoff_digest_sha256') or ''}`",
            f"- Upload receipt digest: `{static_upload_receipt_smoke.get('upload_receipt_digest_sha256') or ''}`",
            f"- Upload receipt JSON: `{static_upload_receipt_smoke.get('upload_receipt_json_path') or ''}`",
            f"- Upload receipt Markdown: `{static_upload_receipt_smoke.get('upload_receipt_markdown_path') or ''}`",
            f"- Operator uploaded base URL: `{static_upload_receipt_smoke.get('operator_uploaded_base_url') or ''}`",
            f"- File count: {static_upload_receipt_smoke.get('file_count')}",
            f"- Failures: `{json.dumps(static_upload_receipt_smoke.get('failures') or [])}`",
            "",
            "## Published Static Index Registration Smoke Summary",
            "",
            f"- Result ok: {str(bool(published_static_index_registration_smoke.get('ok'))).lower()}",
            f"- Status: {published_static_index_registration_smoke.get('status') or ''}",
            f"- Elapsed seconds: {published_static_index_registration_smoke.get('elapsed_seconds')}",
            f"- Result path: `{published_static_index_registration_smoke.get('result_path') or ''}`",
            f"- Remote index digest: `{published_static_index_registration_smoke.get('remote_index_digest_sha256') or ''}`",
            f"- Hosted bundle digest: `{published_static_index_registration_smoke.get('hosted_bundle_digest_sha256') or ''}`",
            f"- Static publication digest: `{published_static_index_registration_smoke.get('static_publication_digest_sha256') or ''}`",
            f"- Upload handoff digest: `{published_static_index_registration_smoke.get('upload_handoff_digest_sha256') or ''}`",
            f"- Upload receipt digest: `{published_static_index_registration_smoke.get('upload_receipt_digest_sha256') or ''}`",
            f"- Registration digest: `{published_static_index_registration_smoke.get('published_static_index_registration_digest_sha256') or ''}`",
            f"- Registration JSON: `{published_static_index_registration_smoke.get('published_static_index_registration_json_path') or ''}`",
            f"- Registration Markdown: `{published_static_index_registration_smoke.get('published_static_index_registration_markdown_path') or ''}`",
            f"- Published index URL: `{published_static_index_registration_smoke.get('operator_published_static_index_url') or ''}`",
            f"- File count: {published_static_index_registration_smoke.get('file_count')}",
            f"- Failures: `{json.dumps(published_static_index_registration_smoke.get('failures') or [])}`",
            "",
            *slides,
            "## Authority Boundary",
            "",
            f"- Forbidden authority flags held false: {len(blocked_flags)}/{len(FORBIDDEN_AUTHORITY_FLAGS)}",
            f"- Proof deck log artifact write allowed: {str(bool(authority.get('proof_deck_log_artifact_write_allowed'))).lower()}",
            f"- Proof deck log artifact written: {str(bool(authority.get('proof_deck_log_artifact_written'))).lower()}",
            "",
            "## Blockers",
            "",
            "\n".join(f"- {blocker}" for blocker in deck.get("blockers") or []) or "- None",
            "",
            "## Next Recommended Pass",
            "",
            deck.get("next_recommended_pass") or "",
            "",
        ]
    )


def build_chaser_forge_proof_deck(
    vault_root: str | Path,
    *,
    generated_at: str | None = None,
    slug: str = DEFAULT_SLUG,
    write: bool = False,
) -> dict[str, Any]:
    """Build and optionally write the Chaser Forge proof deck."""

    vault = _vault_path(vault_root)
    timestamp = generated_at or _now_utc()
    evidence: list[dict[str, Any]] = []
    evidence.extend(
        _evidence_item(vault, path, kind="build_log", summary=_build_log_summary(path))
        for path in BUILD_LOG_RELATIVE_PATHS
    )
    evidence.extend(
        _evidence_item(vault, path, kind="doc", summary="current Chaser Forge / Approval Center truth")
        for path in DOC_RELATIVE_PATHS
    )
    visual, visual_blockers, screenshot_refs = _visual_report_summary(vault)
    evidence.append(
        _evidence_item(
            vault,
            VISUAL_QA_REPORT_RELATIVE_PATH,
            kind="visual_qa_report",
            summary="static rendered Approval Center lifecycle proof",
        )
    )
    for shot in screenshot_refs:
        if shot.get("path"):
            evidence.append(
                {
                    "kind": "visual_qa_screenshot",
                    "path": shot["path"],
                    "exists": bool(shot.get("exists")),
                    "required": True,
                    "summary": f"{shot.get('viewport')} rendered Approval Center screenshot",
                    "status_hint": "not_blank" if shot.get("not_blank") else "blank_or_unverified",
                }
            )
    studio_clickthrough, clickthrough_blockers, clickthrough_screenshot_refs = _studio_clickthrough_summary(vault)
    evidence.append(
        _evidence_item(
            vault,
            STUDIO_CLICKTHROUGH_REPORT_RELATIVE_PATH,
            kind="studio_clickthrough_report",
            summary="rendered Studio Chaser Forge proof-deck clickthrough",
            required=False,
        )
    )
    for shot in clickthrough_screenshot_refs:
        if shot.get("path"):
            evidence.append(
                {
                    "kind": "studio_clickthrough_screenshot",
                    "path": shot["path"],
                    "exists": bool(shot.get("exists")),
                    "required": True,
                    "summary": f"{shot.get('viewport')} Studio Chaser Forge proof-deck screenshot",
                    "status_hint": "not_blank" if shot.get("not_blank") else "blank_or_unverified",
                }
            )

    marketplace_bridge, marketplace_bridge_blockers, marketplace_bridge_screenshot_refs = (
        _marketplace_bridge_visual_summary(vault)
    )
    evidence.append(
        _evidence_item(
            vault,
            Path(str(marketplace_bridge.get("report_path") or MARKETPLACE_BRIDGE_VISUAL_QA_REPORT_RELATIVE_PATH)),
            kind="marketplace_bridge_visual_qa_report",
            summary="rendered Studio marketplace import sandbox request bridge visual proof",
        )
    )
    for shot in marketplace_bridge_screenshot_refs:
        if shot.get("path"):
            evidence.append(
                {
                    "kind": "marketplace_bridge_visual_qa_screenshot",
                    "path": shot["path"],
                    "exists": bool(shot.get("exists")),
                    "required": True,
                    "summary": f"{shot.get('viewport')} Studio marketplace bridge screenshot",
                    "status_hint": "not_blank" if shot.get("not_blank") else "blank_or_unverified",
                }
            )

    live_studio_control, live_studio_control_blockers = _live_studio_control_summary(vault)
    evidence.append(
        _evidence_item(
            vault,
            Path(str(live_studio_control.get("report_path") or LIVE_STUDIO_CONTROL_PROOF_REPORT_RELATIVE_PATH)),
            kind="live_studio_control_proof_report",
            summary="live StudioAPI control proof for governed Chaser Forge marketplace install",
        )
    )

    operator_use, operator_use_blockers, operator_use_screenshot_refs = _operator_use_studio_summary(vault)
    evidence.append(
        _evidence_item(
            vault,
            Path(str(operator_use.get("report_path") or OPERATOR_USE_STUDIO_PROOF_REPORT_RELATIVE_PATH)),
            kind="operator_use_studio_proof_report",
            summary="rendered Studio button-click proof for Chaser Forge marketplace publish/install",
        )
    )
    for shot in operator_use_screenshot_refs:
        if shot.get("path"):
            evidence.append(
                {
                    "kind": "operator_use_studio_proof_screenshot",
                    "path": shot["path"],
                    "exists": bool(shot.get("exists")),
                    "required": True,
                    "summary": f"{shot.get('step')} {shot.get('viewport')} Studio operator-use screenshot",
                    "status_hint": "not_blank" if shot.get("not_blank") else "blank_or_unverified",
                }
            )
    operator_use_closeout_smoke, operator_use_closeout_smoke_blockers = _operator_use_closeout_smoke_summary(vault)
    evidence.append(
        _evidence_item(
            vault,
            OPERATOR_USE_CLOSEOUT_SMOKE_RESULT_RELATIVE_PATH,
            kind="operator_use_closeout_smoke_result",
            summary="direct python -u closeout smoke for Chaser Forge marketplace operator-use proof",
        )
    )
    local_marketplace_library_smoke, local_marketplace_library_smoke_blockers = _local_marketplace_library_smoke_summary(vault)
    evidence.append(
        _evidence_item(
            vault,
            LOCAL_MARKETPLACE_LIBRARY_SMOKE_RESULT_RELATIVE_PATH,
            kind="local_marketplace_library_smoke_result",
            summary="direct StudioAPI smoke for read-only Local Marketplace Library use",
        )
    )
    remote_distribution_smoke, remote_distribution_smoke_blockers = _remote_distribution_smoke_summary(vault)
    evidence.append(
        _evidence_item(
            vault,
            REMOTE_DISTRIBUTION_SMOKE_RESULT_RELATIVE_PATH,
            kind="remote_distribution_smoke_result",
            summary="direct StudioAPI smoke for governed Remote Distribution foundation",
        )
    )
    hosted_marketplace_export_bundle_smoke, hosted_marketplace_export_bundle_smoke_blockers = (
        _hosted_marketplace_export_bundle_smoke_summary(vault)
    )
    evidence.append(
        _evidence_item(
            vault,
            HOSTED_MARKETPLACE_EXPORT_BUNDLE_SMOKE_RESULT_RELATIVE_PATH,
            kind="hosted_marketplace_export_bundle_smoke_result",
            summary="direct StudioAPI smoke for governed hosted marketplace export bundle",
        )
    )
    static_host_publication_smoke, static_host_publication_smoke_blockers = _static_host_publication_smoke_summary(vault)
    evidence.append(
        _evidence_item(
            vault,
            STATIC_HOST_PUBLICATION_SMOKE_RESULT_RELATIVE_PATH,
            kind="static_host_publication_smoke_result",
            summary="direct StudioAPI smoke for governed static-host publication proof",
        )
    )
    static_upload_handoff_smoke, static_upload_handoff_smoke_blockers = _static_upload_handoff_smoke_summary(vault)
    evidence.append(
        _evidence_item(
            vault,
            STATIC_UPLOAD_HANDOFF_SMOKE_RESULT_RELATIVE_PATH,
            kind="static_upload_handoff_smoke_result",
            summary="direct StudioAPI smoke for governed static-host upload handoff",
        )
    )
    static_upload_receipt_smoke, static_upload_receipt_smoke_blockers = _static_upload_receipt_smoke_summary(vault)
    evidence.append(
        _evidence_item(
            vault,
            STATIC_UPLOAD_RECEIPT_SMOKE_RESULT_RELATIVE_PATH,
            kind="static_upload_receipt_smoke_result",
            summary="direct StudioAPI smoke for governed static-host upload receipt",
        )
    )
    (
        published_static_index_registration_smoke,
        published_static_index_registration_smoke_blockers,
    ) = _published_static_index_registration_smoke_summary(vault)
    evidence.append(
        _evidence_item(
            vault,
            PUBLISHED_STATIC_INDEX_REGISTRATION_SMOKE_RESULT_RELATIVE_PATH,
            kind="published_static_index_registration_smoke_result",
            summary="direct StudioAPI smoke for governed published static index registration",
        )
    )

    missing_evidence = [item["path"] for item in evidence if item.get("required") and not item.get("exists")]
    blockers = [f"missing_required_evidence:{path}" for path in missing_evidence]
    blockers.extend(visual_blockers)
    blockers.extend(clickthrough_blockers)
    blockers.extend(marketplace_bridge_blockers)
    blockers.extend(live_studio_control_blockers)
    blockers.extend(operator_use_blockers)
    blockers.extend(operator_use_closeout_smoke_blockers)
    blockers.extend(local_marketplace_library_smoke_blockers)
    blockers.extend(remote_distribution_smoke_blockers)
    blockers.extend(hosted_marketplace_export_bundle_smoke_blockers)
    blockers.extend(static_host_publication_smoke_blockers)
    blockers.extend(static_upload_handoff_smoke_blockers)
    blockers.extend(static_upload_receipt_smoke_blockers)
    blockers.extend(published_static_index_registration_smoke_blockers)
    authority = _authority(write=write, written=False)
    blockers.extend(f"forbidden_authority_flag_true:{flag}" for flag in _validate_authority(authority))
    blockers = list(dict.fromkeys(blockers))
    ok = not blockers
    markdown_path, json_path = _deck_paths(vault, slug)
    writes: list[str] = []

    deck: dict[str, Any] = {
        "ok": ok,
        "surface": PROOF_DECK_SURFACE_ID,
        "schema_version": PROOF_DECK_SCHEMA_VERSION,
        "status": "COMPLETE / PROOF DECK READY" if ok else "PARTIAL / PROOF DECK BLOCKED BY MISSING EVIDENCE",
        "feature_status": "COMPLETE / GOVERNED CHASER FORGE MARKETPLACE, PUBLISHED STATIC INDEX REGISTRATION, STATIC HOST UPLOAD RECEIPT, STATIC HOST UPLOAD HANDOFF, STATIC HOST PUBLICATION PROOF, HOSTED EXPORT BUNDLE, REMOTE DISTRIBUTION FOUNDATION, AND STUDIO UI VERIFIED",
        "artifact_role": "log-only proof deck over existing Forge implementation, marketplace bridge, remote distribution foundation, hosted export bundle, static-host publication proof, static-host upload handoff, static-host upload receipt, published static index registration, live Studio controls, and visual QA evidence",
        "date": timestamp[:10],
        "generated_at": timestamp,
        "runtime": "Codex",
        "session_descriptor": "chaser-forge-published-static-index-registration",
        "vault_root": str(vault),
        "write_requested": write,
        "write_executed": False,
        "read_only": not write,
        "log_only": True,
        "output_root": OUTPUT_ROOT.as_posix(),
        "markdown_path": _relative_to_vault(vault, markdown_path),
        "json_path": _relative_to_vault(vault, json_path),
        "writes": writes,
        "evidence_matrix": evidence,
        "visual_qa": visual,
        "studio_clickthrough": studio_clickthrough,
        "marketplace_bridge_visual_qa": marketplace_bridge,
        "live_studio_control_proof": live_studio_control,
        "operator_use_studio_proof": operator_use,
        "operator_use_closeout_smoke": operator_use_closeout_smoke,
        "local_marketplace_library_smoke": local_marketplace_library_smoke,
        "remote_distribution_smoke": remote_distribution_smoke,
        "hosted_marketplace_export_bundle_smoke": hosted_marketplace_export_bundle_smoke,
        "static_host_publication_smoke": static_host_publication_smoke,
        "static_upload_handoff_smoke": static_upload_handoff_smoke,
        "static_upload_receipt_smoke": static_upload_receipt_smoke,
        "published_static_index_registration_smoke": published_static_index_registration_smoke,
        "slides": _build_slides(
            evidence=evidence,
            visual=visual,
            studio_clickthrough=studio_clickthrough,
            marketplace_bridge=marketplace_bridge,
            live_studio_control=live_studio_control,
            operator_use=operator_use,
            operator_use_closeout_smoke=operator_use_closeout_smoke,
            local_marketplace_library_smoke=local_marketplace_library_smoke,
            remote_distribution_smoke=remote_distribution_smoke,
            hosted_marketplace_export_bundle_smoke=hosted_marketplace_export_bundle_smoke,
            static_host_publication_smoke=static_host_publication_smoke,
            static_upload_handoff_smoke=static_upload_handoff_smoke,
            static_upload_receipt_smoke=static_upload_receipt_smoke,
            published_static_index_registration_smoke=published_static_index_registration_smoke,
            blockers=blockers,
        ),
        "authority": authority,
        "blockers": blockers,
        "next_recommended_pass": NEXT_RECOMMENDED_PASS,
    }

    if write:
        writes = [_relative_to_vault(vault, markdown_path), _relative_to_vault(vault, json_path)]
        deck["writes"] = writes
        deck["write_executed"] = True
        deck["read_only"] = False
        deck["authority"] = _authority(write=True, written=True)
        _write_text(markdown_path, render_chaser_forge_proof_deck_markdown(deck))
        _write_text(json_path, json.dumps(deck, indent=2, sort_keys=True, default=str) + "\n")

    return deck


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the Chaser Forge proof deck.")
    parser.add_argument("--vault-root", default=".", help="Path to the ChaseOS vault root.")
    parser.add_argument("--slug", default=DEFAULT_SLUG, help="Artifact slug for Markdown/JSON outputs.")
    parser.add_argument("--generated-at", default=None, help="Override generated_at timestamp.")
    parser.add_argument("--write", action="store_true", help="Write Markdown/JSON artifacts under 07_LOGS/Workflow-Proofs.")
    parser.add_argument("--json", action="store_true", help="Print the deck JSON envelope.")
    args = parser.parse_args(argv)

    deck = build_chaser_forge_proof_deck(
        args.vault_root,
        generated_at=args.generated_at,
        slug=args.slug,
        write=args.write,
    )
    if args.json:
        print(json.dumps(deck, indent=2, sort_keys=True, default=str))
    else:
        print(render_chaser_forge_proof_deck_markdown(deck))
    return 0 if deck.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
