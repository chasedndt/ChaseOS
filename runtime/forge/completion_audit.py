"""Completion audit for governed Chaser Forge marketplace and Studio wiring.

The audit certifies the repo-local, approval-gated Chaser Forge marketplace,
static-host upload handoff, static-host upload receipt, published static index
registration, install lifecycle,
Studio UI wiring, proof chain, and canonical registration.
It does not grant ambient remote marketplace, payment/license mutation,
provider, Agent Bus, memory, R&D truth-state, protected-core, or canonical
mutation authority.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from runtime.forge.panel import build_chaser_forge_panel


COMPLETION_AUDIT_SCHEMA_VERSION = "forge.marketplace_completion_audit.v1"
COMPLETION_AUDIT_SURFACE_ID = "chaser_forge_marketplace_completion_audit"
DEFAULT_SLUG = "2026-05-21_chaser-forge-marketplace-completion-audit"
OUTPUT_ROOT = Path("07_LOGS") / "Workflow-Proofs"
FEATURE_REGISTER_PATH = Path("06_AGENTS") / "Feature-Register.md"
FEATURE_FIT_REGISTER_PATH = Path("06_AGENTS") / "Feature-Fit-Register.md"
FORGE_COMPLETION_STATUS = (
    "COMPLETE / GOVERNED CHASER FORGE MARKETPLACE, PUBLISHED STATIC INDEX REGISTRATION, STATIC HOST "
    "UPLOAD RECEIPT, STATIC HOST UPLOAD HANDOFF, STATIC HOST PUBLICATION PROOF, HOSTED EXPORT "
    "BUNDLE, REMOTE DISTRIBUTION FOUNDATION, AND STUDIO UI VERIFIED"
)
MARKETPLACE_STATUS = (
    "COMPLETE / CHASEOS-OWNED LOCAL PUBLIC CATALOG, GOVERNED PUBLISHED STATIC INDEX REGISTRATION, "
    "GOVERNED STATIC HOST UPLOAD RECEIPT, GOVERNED STATIC HOST UPLOAD HANDOFF, GOVERNED STATIC "
    "HOST PUBLICATION PROOF, GOVERNED HOSTED EXPORT BUNDLE, GOVERNED REMOTE DISTRIBUTION FOUNDATION, "
    "AND GOVERNED INSTALL VERIFIED"
)
NEXT_RECOMMENDED_PASS = "operator-authorize-live-url-fetch-verification-or-external-registry-publication"

FORBIDDEN_AUTHORITY_FLAGS = (
    "remote_marketplace_call_allowed",
    "third_party_marketplace_exchange_allowed",
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

REQUIRED_TRUE_SUMMARY_FLAGS = (
    "demo_manifest_valid",
    "sandbox_approval_preview_ready",
    "sandbox_registry_writer_built",
    "live_install_approval_packet_built",
    "live_install_executor_built",
    "rollback_approval_packet_built",
    "rollback_executor_built",
    "approval_center_decision_handoff_built",
    "operator_decision_form_contract_built",
    "decision_bound_executor_validation_ready",
    "executor_requires_decision_sidecar",
    "proof_deck_packaged",
    "proof_deck_log_only",
    "proof_deck_read_only",
    "live_studio_control_proof_verified",
    "operator_use_studio_proof_verified",
    "marketplace_export_package_built",
    "marketplace_export_preview_ready",
    "marketplace_import_preview_built",
    "marketplace_import_preview_ready",
    "marketplace_import_approval_packet_built",
    "marketplace_import_approval_preview_ready",
    "marketplace_import_sandbox_request_bridge_built",
    "marketplace_package_write_enabled_by_panel",
    "marketplace_catalog_built",
    "marketplace_catalog_ready",
    "marketplace_publish_built",
    "marketplace_publish_preview_ready",
    "marketplace_publish_allowed",
    "marketplace_publish_write_enabled_by_panel",
    "marketplace_import_approval_consumption_allowed",
    "marketplace_import_approval_consumption_requires_install_executor",
    "marketplace_import_sandbox_execution_allowed",
    "marketplace_install_executor_built",
    "marketplace_governed_auto_install_available",
    "marketplace_auto_install_allowed",
    "marketplace_auto_install_requires_approval",
    "marketplace_local_library_built",
    "marketplace_local_library_ready",
    "marketplace_local_library_read_only",
    "marketplace_local_library_remote_exchange_blocked",
    "marketplace_remote_distribution_built",
    "marketplace_remote_distribution_ready",
    "marketplace_remote_index_write_digest_gated",
    "marketplace_remote_ingest_preview_ready",
    "marketplace_remote_ingest_digest_gated",
    "marketplace_remote_network_calls_blocked",
    "marketplace_remote_payment_mutation_blocked",
    "marketplace_remote_publisher_attestation_verified",
    "marketplace_hosted_export_bundle_built",
    "marketplace_hosted_export_bundle_ready",
    "marketplace_hosted_export_bundle_digest_gated",
    "marketplace_hosted_export_manual_static_ready",
    "marketplace_hosted_export_network_publish_blocked",
    "marketplace_hosted_export_payment_mutation_blocked",
    "marketplace_static_host_publication_built",
    "marketplace_static_host_publication_ready",
    "marketplace_static_host_publication_digest_gated",
    "marketplace_static_host_publication_manual_upload_ready",
    "marketplace_static_host_publication_network_upload_blocked",
    "marketplace_static_host_publication_payment_mutation_blocked",
    "marketplace_static_upload_handoff_built",
    "marketplace_static_upload_handoff_ready",
    "marketplace_static_upload_handoff_digest_gated",
    "marketplace_static_upload_handoff_manual_action_required",
    "marketplace_static_upload_handoff_network_upload_blocked",
    "marketplace_static_upload_handoff_external_registry_blocked",
    "marketplace_static_upload_receipt_built",
    "marketplace_static_upload_receipt_ready",
    "marketplace_static_upload_receipt_digest_gated",
    "marketplace_static_upload_receipt_operator_statement_required",
    "marketplace_static_upload_receipt_network_fetch_blocked",
    "marketplace_static_upload_receipt_external_registry_blocked",
    "marketplace_published_static_index_registration_built",
    "marketplace_published_static_index_registration_ready",
    "marketplace_published_static_index_registration_digest_gated",
    "marketplace_published_static_index_registration_operator_statement_required",
    "marketplace_published_static_index_registration_network_fetch_blocked",
    "marketplace_published_static_index_registration_external_registry_blocked",
    "marketplace_published_static_index_registration_live_url_unverified",
)

REQUIRED_FALSE_SUMMARY_FLAGS = (
    "generated_core_mutation_allowed",
    "installer_writes_enabled",
    "sandbox_registry_execution_enabled",
    "live_install_execution_enabled",
    "rollback_execution_enabled",
    "operator_decision_form_write_enabled",
    "operator_decision_form_generic_control",
    "approval_decision_write_enabled_by_panel",
    "approval_decision_consumption_allowed",
    "public_marketplace_deferred",
    "marketplace_unauthorized_auto_install_allowed",
)


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _relative_to_vault(vault: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(vault.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _safe_slug(value: str) -> str:
    slug = "".join(char if char.isalnum() or char in "._-" else "-" for char in value.strip()).strip("-")
    if not slug or slug in {".", ".."} or ".." in slug:
        raise ValueError("completion audit slug is invalid")
    return slug


def _audit_paths(vault: Path, slug: str) -> tuple[Path, Path]:
    root = (vault / OUTPUT_ROOT).resolve()
    safe = _safe_slug(slug)
    markdown_path = (root / f"{safe}.md").resolve()
    json_path = (root / f"{safe}.json").resolve()
    for path in (markdown_path, json_path):
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise ValueError("Chaser Forge completion audit output must stay inside 07_LOGS/Workflow-Proofs") from exc
    return markdown_path, json_path


def _doc_registration(vault: Path) -> dict[str, Any]:
    feature_register = vault / FEATURE_REGISTER_PATH
    fit_register = vault / FEATURE_FIT_REGISTER_PATH
    feature_text = _read_text(feature_register)
    fit_text = _read_text(fit_register)
    return {
        "feature_register_path": FEATURE_REGISTER_PATH.as_posix(),
        "feature_register_exists": feature_register.is_file(),
        "feature_register_mentions_chaser_forge": "Chaser Forge" in feature_text,
        "feature_register_marketplace_complete": "GOVERNED CHASER FORGE MARKETPLACE" in feature_text
        and "PUBLISHED STATIC INDEX REGISTRATION" in feature_text
        and "STATIC HOST UPLOAD RECEIPT" in feature_text
        and "STATIC HOST UPLOAD HANDOFF" in feature_text
        and "STATIC HOST PUBLICATION PROOF" in feature_text
        and "HOSTED EXPORT BUNDLE" in feature_text
        and "STUDIO UI" in feature_text,
        "feature_fit_register_path": FEATURE_FIT_REGISTER_PATH.as_posix(),
        "feature_fit_register_exists": fit_register.is_file(),
        "feature_fit_register_mentions_chaser_forge": "Chaser Forge" in fit_text,
        "feature_fit_register_marketplace_complete": "GOVERNED CHASER FORGE MARKETPLACE" in fit_text
        and "PUBLISHED STATIC INDEX REGISTRATION" in fit_text
        and "STATIC HOST UPLOAD RECEIPT" in fit_text
        and "STATIC HOST UPLOAD HANDOFF" in fit_text
        and "STATIC HOST PUBLICATION PROOF" in fit_text
        and "HOSTED EXPORT BUNDLE" in fit_text
        and "STUDIO UI" in fit_text,
    }


def _authority(write: bool, written: bool) -> dict[str, Any]:
    authority = {flag: False for flag in FORBIDDEN_AUTHORITY_FLAGS}
    authority.update(
        {
            "completion_audit_log_write_requested": bool(write),
            "completion_audit_log_written": bool(written),
            "log_only": True,
        }
    )
    return authority


def _blockers(audit: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    panel = audit.get("panel_summary") or {}
    blockers.extend(f"panel_summary_flag_false:{flag}" for flag in REQUIRED_TRUE_SUMMARY_FLAGS if panel.get(flag) is not True)
    blockers.extend(f"panel_summary_flag_true:{flag}" for flag in REQUIRED_FALSE_SUMMARY_FLAGS if panel.get(flag) is not False)
    proof_deck = audit.get("proof_deck") or {}
    if proof_deck.get("ok") is not True:
        blockers.append("proof_deck_not_complete")
    if proof_deck.get("feature_status") != FORGE_COMPLETION_STATUS:
        blockers.append("proof_deck_feature_status_not_marketplace_complete")
    live_proof = audit.get("live_studio_control_proof") or {}
    if live_proof.get("ok") is not True:
        blockers.append("live_studio_control_proof_not_complete")
    operator_use_proof = audit.get("operator_use_studio_proof") or {}
    if operator_use_proof.get("ok") is not True:
        blockers.append("operator_use_studio_proof_not_complete")
    operator_use_closeout_smoke = audit.get("operator_use_closeout_smoke") or {}
    if operator_use_closeout_smoke.get("ok") is not True:
        blockers.append("operator_use_closeout_smoke_not_complete")
    local_marketplace_library_smoke = audit.get("local_marketplace_library_smoke") or {}
    if local_marketplace_library_smoke.get("ok") is not True:
        blockers.append("local_marketplace_library_smoke_not_complete")
    remote_distribution_smoke = audit.get("remote_distribution_smoke") or {}
    if remote_distribution_smoke.get("ok") is not True:
        blockers.append("remote_distribution_smoke_not_complete")
    hosted_marketplace_export_bundle_smoke = audit.get("hosted_marketplace_export_bundle_smoke") or {}
    if hosted_marketplace_export_bundle_smoke.get("ok") is not True:
        blockers.append("hosted_marketplace_export_bundle_smoke_not_complete")
    static_host_publication_smoke = audit.get("static_host_publication_smoke") or {}
    if static_host_publication_smoke.get("ok") is not True:
        blockers.append("static_host_publication_smoke_not_complete")
    static_upload_handoff_smoke = audit.get("static_upload_handoff_smoke") or {}
    if static_upload_handoff_smoke.get("ok") is not True:
        blockers.append("static_upload_handoff_smoke_not_complete")
    static_upload_receipt_smoke = audit.get("static_upload_receipt_smoke") or {}
    if static_upload_receipt_smoke.get("ok") is not True:
        blockers.append("static_upload_receipt_smoke_not_complete")
    published_static_index_registration_smoke = audit.get("published_static_index_registration_smoke") or {}
    if published_static_index_registration_smoke.get("ok") is not True:
        blockers.append("published_static_index_registration_smoke_not_complete")
    registration = audit.get("registration") or {}
    for key in (
        "feature_register_exists",
        "feature_register_mentions_chaser_forge",
        "feature_register_marketplace_complete",
        "feature_fit_register_exists",
        "feature_fit_register_mentions_chaser_forge",
        "feature_fit_register_marketplace_complete",
    ):
        if registration.get(key) is not True:
            blockers.append(f"registration_check_failed:{key}")
    authority = audit.get("authority") or {}
    blockers.extend(f"forbidden_authority_flag_true:{flag}" for flag in FORBIDDEN_AUTHORITY_FLAGS if authority.get(flag) is not False)
    return list(dict.fromkeys(blockers))


def render_chaser_forge_completion_audit(audit: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Chaser Forge Marketplace Completion Audit",
            "",
            f"- Date: {audit.get('date')}",
            f"- Runtime: {audit.get('runtime')}",
            f"- Session descriptor: `{audit.get('session_descriptor')}`",
            f"- Status: {audit.get('status')}",
            f"- Forge completion status: {audit.get('forge_completion_status')}",
            f"- Marketplace status: {audit.get('marketplace_status')}",
            "",
            "## Registration",
            "",
            f"- Feature Register: {str((audit.get('registration') or {}).get('feature_register_marketplace_complete')).lower()}",
            f"- Feature Fit Register: {str((audit.get('registration') or {}).get('feature_fit_register_marketplace_complete')).lower()}",
            "",
            "## Verified Marketplace",
            "",
            "- StudioAPI sandbox, live, rollback, catalog publish, marketplace import approval, sandbox approval, and marketplace install controls are backed by live temp-fixture proof evidence.",
            "- The production Studio button flow is backed by rendered operator-use proof with final publish/install status visible after panel refresh.",
            "- The operator-use closeout is backed by a direct `python -u` smoke result with explicit JSON output and faulthandler timeout, replacing the hanging pytest wrapper.",
            "- The Local Marketplace Library is backed by a direct StudioAPI smoke that verifies listed versus installed state, frontend/API wiring, read-only authority, and unchanged real vault registry/catalog files.",
            "- The proof deck is complete and log-only.",
            "- The governed remote distribution foundation is backed by a direct StudioAPI smoke that verifies index write, trusted listing ingest, UI/API wiring, and unchanged real vault registry/catalog/remote-index files.",
            "- The governed hosted export bundle is backed by a direct StudioAPI smoke that verifies digest-gated manual static-host bundle write, UI/API wiring, no credentials, and unchanged real vault registry/catalog/remote-index/hosted-bundle files.",
            "- The governed static-host publication proof is backed by a direct StudioAPI smoke that verifies upload-ready files, remote/hosted/static digest gates, UI/API wiring, and unchanged real vault registry/catalog/remote-index/hosted-bundle/static-publication files.",
            "- The governed static-host upload handoff is backed by a direct StudioAPI smoke that verifies digest-gated local JSON/Markdown operator handoff artifacts, UI/API wiring, and unchanged real vault registry/catalog/remote-index/hosted-bundle/static-publication/upload-handoff files.",
            "- The governed static-host upload receipt is backed by a direct StudioAPI smoke that verifies digest-gated local JSON/Markdown operator receipt artifacts, exact receipt statement gating, network fetch blocked posture, UI/API wiring, and unchanged real vault registry/catalog/remote-index/hosted-bundle/static-publication/upload-handoff/upload-receipt files.",
            "- The governed published static index registration is backed by a direct StudioAPI smoke that verifies digest-gated local JSON/Markdown registration artifacts, exact registration statement gating, live URL fetch blocked posture, UI/API wiring, and unchanged real vault registry/catalog/distribution artifact paths.",
            "- The ChaseOS-owned local public catalog, governed published static index registration, governed static-host upload receipt, governed static-host upload handoff, governed static-host publication proof, governed hosted export bundle, governed remote distribution foundation, and governed install path are complete; ambient live remote marketplace calls, untrusted exchange, external registry mutation, and payment/license mutation remain blocked by design.",
            f"- Remote Distribution smoke: {str(((audit.get('remote_distribution_smoke') or {}).get('ok'))).lower()} `{(audit.get('remote_distribution_smoke') or {}).get('result_path') or ''}`",
            f"- Hosted Export Bundle smoke: {str(((audit.get('hosted_marketplace_export_bundle_smoke') or {}).get('ok'))).lower()} `{(audit.get('hosted_marketplace_export_bundle_smoke') or {}).get('result_path') or ''}`",
            f"- Static Host Publication smoke: {str(((audit.get('static_host_publication_smoke') or {}).get('ok'))).lower()} `{(audit.get('static_host_publication_smoke') or {}).get('result_path') or ''}`",
            f"- Static Upload Handoff smoke: {str(((audit.get('static_upload_handoff_smoke') or {}).get('ok'))).lower()} `{(audit.get('static_upload_handoff_smoke') or {}).get('result_path') or ''}`",
            f"- Static Upload Receipt smoke: {str(((audit.get('static_upload_receipt_smoke') or {}).get('ok'))).lower()} `{(audit.get('static_upload_receipt_smoke') or {}).get('result_path') or ''}`",
            f"- Published Static Index Registration smoke: {str(((audit.get('published_static_index_registration_smoke') or {}).get('ok'))).lower()} `{(audit.get('published_static_index_registration_smoke') or {}).get('result_path') or ''}`",
            "",
            "## Blockers",
            "",
            "\n".join(f"- {blocker}" for blocker in audit.get("blockers") or []) or "- None",
            "",
        ]
    )


def build_chaser_forge_completion_audit(
    vault_root: str | Path,
    *,
    generated_at: str | None = None,
    slug: str = DEFAULT_SLUG,
    write: bool = False,
) -> dict[str, Any]:
    """Build and optionally write the Chaser Forge marketplace completion audit."""

    vault = _vault_path(vault_root)
    timestamp = generated_at or _now_utc()
    panel = build_chaser_forge_panel(vault)
    proof_deck = panel.get("proof_deck") if isinstance(panel.get("proof_deck"), dict) else {}
    live_proof = proof_deck.get("live_studio_control_proof") if isinstance(proof_deck.get("live_studio_control_proof"), dict) else {}
    operator_use_proof = proof_deck.get("operator_use_studio_proof") if isinstance(proof_deck.get("operator_use_studio_proof"), dict) else {}
    operator_use_closeout_smoke = (
        proof_deck.get("operator_use_closeout_smoke")
        if isinstance(proof_deck.get("operator_use_closeout_smoke"), dict)
        else {}
    )
    local_marketplace_library_smoke = (
        proof_deck.get("local_marketplace_library_smoke")
        if isinstance(proof_deck.get("local_marketplace_library_smoke"), dict)
        else {}
    )
    remote_distribution_smoke = (
        proof_deck.get("remote_distribution_smoke")
        if isinstance(proof_deck.get("remote_distribution_smoke"), dict)
        else {}
    )
    hosted_marketplace_export_bundle_smoke = (
        proof_deck.get("hosted_marketplace_export_bundle_smoke")
        if isinstance(proof_deck.get("hosted_marketplace_export_bundle_smoke"), dict)
        else {}
    )
    static_host_publication_smoke = (
        proof_deck.get("static_host_publication_smoke")
        if isinstance(proof_deck.get("static_host_publication_smoke"), dict)
        else {}
    )
    static_upload_handoff_smoke = (
        proof_deck.get("static_upload_handoff_smoke")
        if isinstance(proof_deck.get("static_upload_handoff_smoke"), dict)
        else {}
    )
    static_upload_receipt_smoke = (
        proof_deck.get("static_upload_receipt_smoke")
        if isinstance(proof_deck.get("static_upload_receipt_smoke"), dict)
        else {}
    )
    published_static_index_registration_smoke = (
        proof_deck.get("published_static_index_registration_smoke")
        if isinstance(proof_deck.get("published_static_index_registration_smoke"), dict)
        else {}
    )
    markdown_path, json_path = _audit_paths(vault, slug)
    audit: dict[str, Any] = {
        "ok": False,
        "surface": COMPLETION_AUDIT_SURFACE_ID,
        "schema_version": COMPLETION_AUDIT_SCHEMA_VERSION,
        "status": "PARTIAL / CHASER FORGE MARKETPLACE COMPLETION AUDIT BLOCKED",
        "forge_completion_status": FORGE_COMPLETION_STATUS,
        "marketplace_status": MARKETPLACE_STATUS,
        "date": timestamp[:10],
        "generated_at": timestamp,
        "runtime": "Codex",
        "session_descriptor": "chaser-forge-published-static-index-registration",
        "vault_root": str(vault),
        "write_requested": write,
        "write_executed": False,
        "markdown_path": _relative_to_vault(vault, markdown_path),
        "json_path": _relative_to_vault(vault, json_path),
        "panel_status": panel.get("status") or "",
        "panel_summary": panel.get("summary") or {},
        "proof_deck": {
            "ok": proof_deck.get("ok"),
            "status": proof_deck.get("status") or "",
            "feature_status": proof_deck.get("feature_status") or "",
            "blockers": list(proof_deck.get("blockers") or []),
            "markdown_path": proof_deck.get("markdown_path") or "",
            "json_path": proof_deck.get("json_path") or "",
        },
        "live_studio_control_proof": {
            "ok": live_proof.get("ok"),
            "status": live_proof.get("status") or "",
            "report_path": live_proof.get("report_path") or "",
            "sandbox_registry_written": live_proof.get("sandbox_registry_written"),
            "live_install_executed": live_proof.get("live_install_executed"),
            "rollback_executed": live_proof.get("rollback_executed"),
            "catalog_listing_written": live_proof.get("catalog_listing_written"),
            "marketplace_install_executed": live_proof.get("marketplace_install_executed"),
            "marketplace_install_registry_written": live_proof.get("marketplace_install_registry_written"),
            "marketplace_install_exact_once_marker_reserved": live_proof.get(
                "marketplace_install_exact_once_marker_reserved"
            ),
        },
        "operator_use_studio_proof": {
            "ok": operator_use_proof.get("ok"),
            "status": operator_use_proof.get("status") or "",
            "report_path": operator_use_proof.get("report_path") or "",
            "publish_status_visible_after_refresh": operator_use_proof.get("publish_status_visible_after_refresh"),
            "install_status_visible_after_refresh": operator_use_proof.get("install_status_visible_after_refresh"),
            "required_api_methods_called": operator_use_proof.get("required_api_methods_called"),
            "fixture_registry_written": operator_use_proof.get("fixture_registry_written"),
            "fixture_exact_once_marker_written": operator_use_proof.get("fixture_exact_once_marker_written"),
        },
        "operator_use_closeout_smoke": {
            "ok": operator_use_closeout_smoke.get("ok"),
            "status": operator_use_closeout_smoke.get("status") or "",
            "result_path": operator_use_closeout_smoke.get("result_path") or "",
            "report_path": operator_use_closeout_smoke.get("report_path") or "",
            "elapsed_seconds": operator_use_closeout_smoke.get("elapsed_seconds"),
            "failures": list(operator_use_closeout_smoke.get("failures") or []),
        },
        "local_marketplace_library_smoke": {
            "ok": local_marketplace_library_smoke.get("ok"),
            "status": local_marketplace_library_smoke.get("status") or "",
            "result_path": local_marketplace_library_smoke.get("result_path") or "",
            "elapsed_seconds": local_marketplace_library_smoke.get("elapsed_seconds"),
            "library_item_count": local_marketplace_library_smoke.get("library_item_count"),
            "listed_installed_count": local_marketplace_library_smoke.get("listed_installed_count"),
            "installed_unlisted_count": local_marketplace_library_smoke.get("installed_unlisted_count"),
            "marketplace_install_executed": local_marketplace_library_smoke.get("marketplace_install_executed"),
            "registry_written_in_fixture": local_marketplace_library_smoke.get("registry_written_in_fixture"),
            "failures": list(local_marketplace_library_smoke.get("failures") or []),
        },
        "remote_distribution_smoke": {
            "ok": remote_distribution_smoke.get("ok"),
            "status": remote_distribution_smoke.get("status") or "",
            "result_path": remote_distribution_smoke.get("result_path") or "",
            "elapsed_seconds": remote_distribution_smoke.get("elapsed_seconds"),
            "remote_index_digest_sha256": remote_distribution_smoke.get("remote_index_digest_sha256"),
            "listing_digest_sha256": remote_distribution_smoke.get("listing_digest_sha256"),
            "ingested_listing_id": remote_distribution_smoke.get("ingested_listing_id"),
            "catalog_entry_count": remote_distribution_smoke.get("catalog_entry_count"),
            "library_item_count": remote_distribution_smoke.get("library_item_count"),
            "failures": list(remote_distribution_smoke.get("failures") or []),
        },
        "hosted_marketplace_export_bundle_smoke": {
            "ok": hosted_marketplace_export_bundle_smoke.get("ok"),
            "status": hosted_marketplace_export_bundle_smoke.get("status") or "",
            "result_path": hosted_marketplace_export_bundle_smoke.get("result_path") or "",
            "elapsed_seconds": hosted_marketplace_export_bundle_smoke.get("elapsed_seconds"),
            "remote_index_digest_sha256": hosted_marketplace_export_bundle_smoke.get("remote_index_digest_sha256"),
            "hosted_bundle_digest_sha256": hosted_marketplace_export_bundle_smoke.get("hosted_bundle_digest_sha256"),
            "hosted_bundle_artifact_path": hosted_marketplace_export_bundle_smoke.get("hosted_bundle_artifact_path"),
            "entry_count": hosted_marketplace_export_bundle_smoke.get("entry_count"),
            "publication_mode": hosted_marketplace_export_bundle_smoke.get("publication_mode"),
            "failures": list(hosted_marketplace_export_bundle_smoke.get("failures") or []),
        },
        "static_host_publication_smoke": {
            "ok": static_host_publication_smoke.get("ok"),
            "status": static_host_publication_smoke.get("status") or "",
            "result_path": static_host_publication_smoke.get("result_path") or "",
            "elapsed_seconds": static_host_publication_smoke.get("elapsed_seconds"),
            "remote_index_digest_sha256": static_host_publication_smoke.get("remote_index_digest_sha256"),
            "hosted_bundle_digest_sha256": static_host_publication_smoke.get("hosted_bundle_digest_sha256"),
            "static_publication_digest_sha256": static_host_publication_smoke.get("static_publication_digest_sha256"),
            "static_publication_dir_path": static_host_publication_smoke.get("static_publication_dir_path"),
            "file_count": static_host_publication_smoke.get("file_count"),
            "failures": list(static_host_publication_smoke.get("failures") or []),
        },
        "static_upload_handoff_smoke": {
            "ok": static_upload_handoff_smoke.get("ok"),
            "status": static_upload_handoff_smoke.get("status") or "",
            "result_path": static_upload_handoff_smoke.get("result_path") or "",
            "elapsed_seconds": static_upload_handoff_smoke.get("elapsed_seconds"),
            "remote_index_digest_sha256": static_upload_handoff_smoke.get("remote_index_digest_sha256"),
            "hosted_bundle_digest_sha256": static_upload_handoff_smoke.get("hosted_bundle_digest_sha256"),
            "static_publication_digest_sha256": static_upload_handoff_smoke.get(
                "static_publication_digest_sha256"
            ),
            "upload_handoff_digest_sha256": static_upload_handoff_smoke.get("upload_handoff_digest_sha256"),
            "upload_handoff_json_path": static_upload_handoff_smoke.get("upload_handoff_json_path"),
            "upload_handoff_markdown_path": static_upload_handoff_smoke.get("upload_handoff_markdown_path"),
            "file_count": static_upload_handoff_smoke.get("file_count"),
            "failures": list(static_upload_handoff_smoke.get("failures") or []),
        },
        "static_upload_receipt_smoke": {
            "ok": static_upload_receipt_smoke.get("ok"),
            "status": static_upload_receipt_smoke.get("status") or "",
            "result_path": static_upload_receipt_smoke.get("result_path") or "",
            "elapsed_seconds": static_upload_receipt_smoke.get("elapsed_seconds"),
            "remote_index_digest_sha256": static_upload_receipt_smoke.get("remote_index_digest_sha256"),
            "hosted_bundle_digest_sha256": static_upload_receipt_smoke.get("hosted_bundle_digest_sha256"),
            "static_publication_digest_sha256": static_upload_receipt_smoke.get(
                "static_publication_digest_sha256"
            ),
            "upload_handoff_digest_sha256": static_upload_receipt_smoke.get("upload_handoff_digest_sha256"),
            "upload_receipt_digest_sha256": static_upload_receipt_smoke.get("upload_receipt_digest_sha256"),
            "upload_receipt_json_path": static_upload_receipt_smoke.get("upload_receipt_json_path"),
            "upload_receipt_markdown_path": static_upload_receipt_smoke.get("upload_receipt_markdown_path"),
            "operator_uploaded_base_url": static_upload_receipt_smoke.get("operator_uploaded_base_url"),
            "file_count": static_upload_receipt_smoke.get("file_count"),
            "failures": list(static_upload_receipt_smoke.get("failures") or []),
        },
        "published_static_index_registration_smoke": {
            "ok": published_static_index_registration_smoke.get("ok"),
            "status": published_static_index_registration_smoke.get("status") or "",
            "result_path": published_static_index_registration_smoke.get("result_path") or "",
            "elapsed_seconds": published_static_index_registration_smoke.get("elapsed_seconds"),
            "remote_index_digest_sha256": published_static_index_registration_smoke.get("remote_index_digest_sha256"),
            "hosted_bundle_digest_sha256": published_static_index_registration_smoke.get("hosted_bundle_digest_sha256"),
            "static_publication_digest_sha256": published_static_index_registration_smoke.get(
                "static_publication_digest_sha256"
            ),
            "upload_handoff_digest_sha256": published_static_index_registration_smoke.get(
                "upload_handoff_digest_sha256"
            ),
            "upload_receipt_digest_sha256": published_static_index_registration_smoke.get(
                "upload_receipt_digest_sha256"
            ),
            "published_static_index_registration_digest_sha256": published_static_index_registration_smoke.get(
                "published_static_index_registration_digest_sha256"
            ),
            "published_static_index_registration_json_path": published_static_index_registration_smoke.get(
                "published_static_index_registration_json_path"
            ),
            "published_static_index_registration_markdown_path": published_static_index_registration_smoke.get(
                "published_static_index_registration_markdown_path"
            ),
            "operator_published_static_index_url": published_static_index_registration_smoke.get(
                "operator_published_static_index_url"
            ),
            "file_count": published_static_index_registration_smoke.get("file_count"),
            "failures": list(published_static_index_registration_smoke.get("failures") or []),
        },
        "registration": _doc_registration(vault),
        "blocked_external_authority": [
            "untrusted third-party package exchange",
            "ambient remote marketplace calls",
            "external registry mutation",
            "payment/license mutation",
            "network fetch verification without explicit future approval",
            "unauthorized auto-install without source-specific approvals",
            "generic Approval Center write controls",
        ],
        "authority": _authority(write=write, written=False),
        "blockers": [],
        "next_recommended_pass": NEXT_RECOMMENDED_PASS,
    }
    audit["blockers"] = _blockers(audit)
    audit["ok"] = not audit["blockers"]
    audit["status"] = (
        "COMPLETE / GOVERNED CHASER FORGE MARKETPLACE, PUBLISHED STATIC INDEX REGISTRATION, STATIC HOST UPLOAD RECEIPT, STATIC HOST UPLOAD HANDOFF, STATIC HOST PUBLICATION PROOF, HOSTED EXPORT BUNDLE, REMOTE DISTRIBUTION FOUNDATION, AND STUDIO UI REGISTERED"
        if audit["ok"]
        else audit["status"]
    )

    if write:
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        audit["write_executed"] = True
        audit["authority"] = _authority(write=True, written=True)
        audit["blockers"] = _blockers(audit)
        audit["ok"] = not audit["blockers"]
        audit["status"] = (
            "COMPLETE / GOVERNED CHASER FORGE MARKETPLACE, PUBLISHED STATIC INDEX REGISTRATION, STATIC HOST UPLOAD RECEIPT, STATIC HOST UPLOAD HANDOFF, STATIC HOST PUBLICATION PROOF, HOSTED EXPORT BUNDLE, REMOTE DISTRIBUTION FOUNDATION, AND STUDIO UI REGISTERED"
            if audit["ok"]
            else "PARTIAL / CHASER FORGE MARKETPLACE COMPLETION AUDIT BLOCKED"
        )
        markdown_path.write_text(render_chaser_forge_completion_audit(audit), encoding="utf-8")
        json_path.write_text(json.dumps(audit, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")

    return audit


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the Chaser Forge marketplace completion audit.")
    parser.add_argument("--vault-root", default=".", help="Path to the ChaseOS vault root.")
    parser.add_argument("--slug", default=DEFAULT_SLUG, help="Artifact slug for Markdown/JSON outputs.")
    parser.add_argument("--generated-at", default=None, help="Override generated_at timestamp.")
    parser.add_argument("--write", action="store_true", help="Write Markdown/JSON artifacts under 07_LOGS/Workflow-Proofs.")
    parser.add_argument("--json", action="store_true", help="Print the audit JSON envelope.")
    args = parser.parse_args(argv)

    audit = build_chaser_forge_completion_audit(
        args.vault_root,
        generated_at=args.generated_at,
        slug=args.slug,
        write=args.write,
    )
    if args.json:
        print(json.dumps(audit, indent=2, sort_keys=True, default=str))
    else:
        print(render_chaser_forge_completion_audit(audit))
    return 0 if audit.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
