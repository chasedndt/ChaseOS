from __future__ import annotations

import json
import os
from pathlib import Path

from runtime.forge.approval_decision import build_forge_approval_decision_handoff
from runtime.forge.panel import build_chaser_forge_panel
from runtime.forge.proof_deck import (
    BUILD_LOG_RELATIVE_PATHS,
    DOC_RELATIVE_PATHS,
    HOSTED_MARKETPLACE_EXPORT_BUNDLE_SMOKE_RESULT_RELATIVE_PATH,
    LIVE_STUDIO_CONTROL_PROOF_FALLBACK_REPORT_RELATIVE_PATH,
    LOCAL_MARKETPLACE_LIBRARY_SMOKE_RESULT_RELATIVE_PATH,
    MARKETPLACE_BRIDGE_VISUAL_QA_FALLBACK_REPORT_RELATIVE_PATH,
    MARKETPLACE_BRIDGE_VISUAL_QA_REPORT_RELATIVE_PATH,
    OPERATOR_USE_CLOSEOUT_SMOKE_RESULT_RELATIVE_PATH,
    OPERATOR_USE_STUDIO_PROOF_REPORT_RELATIVE_PATH,
    PUBLISHED_STATIC_INDEX_REGISTRATION_SMOKE_RESULT_RELATIVE_PATH,
    REMOTE_DISTRIBUTION_SMOKE_RESULT_RELATIVE_PATH,
    STATIC_HOST_PUBLICATION_SMOKE_RESULT_RELATIVE_PATH,
    STATIC_UPLOAD_HANDOFF_SMOKE_RESULT_RELATIVE_PATH,
    STATIC_UPLOAD_RECEIPT_SMOKE_RESULT_RELATIVE_PATH,
    VISUAL_QA_REPORT_RELATIVE_PATH,
)
from runtime.studio.shell.api import StudioAPI
from runtime.studio.shell.panel_registry import build_native_shell_panel_registry


REPO_ROOT = Path(__file__).resolve().parents[2]


def _approve_artifact(vault: Path, artifact_path: Path) -> None:
    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    handoff = build_forge_approval_decision_handoff(
        vault,
        approval_artifact_path=artifact_path,
        decision="approved",
        expected_request_digest=payload["request_digest_sha256"],
        operator_statement=payload["operator_confirmation_text"],
        write_decision=True,
        reviewer_id="operator",
        generated_at="2026-05-20T00:00:00Z",
    )
    assert handoff["ok"] is True, handoff


def _write(path: Path, text: str) -> None:
    target = _io_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def _io_path(path: Path) -> Path:
    resolved = path.resolve()
    if os.name == "nt" and not str(resolved).startswith("\\\\?\\"):
        return Path("\\\\?\\" + str(resolved))
    return resolved


def _seed_proof_deck_evidence(vault: Path) -> None:
    for rel_path in BUILD_LOG_RELATIVE_PATHS:
        _write(vault / rel_path, f"# {rel_path.stem}\n\n- Status: PARTIAL / VERIFIED\n")
    for rel_path in DOC_RELATIVE_PATHS:
        _write(vault / rel_path, f"# {rel_path.stem}\n\nStatus: PARTIAL / VERIFIED\n")
    report = {
        "ok": True,
        "status": "PARTIAL / STATIC UI LIFECYCLE PROOF / VERIFIED",
        "summary": {
            "source_group_visible": True,
            "lifecycle_statuses": [
                "approved_pending_execution",
                "consumed",
                "invalid_packet",
                "pending_operator_review",
                "rejected",
            ],
            "lifecycle_tokens_visible": True,
            "artifact_count": 5,
            "pending_count": 1,
            "ready_count": 2,
            "blocked_count": 2,
            "desktop_and_mobile_checked": True,
        },
        "forge_source_group": {
            "status_counts": {
                "approved_pending_execution": 1,
                "consumed": 1,
                "invalid_packet": 1,
                "pending_operator_review": 1,
                "rejected": 1,
            },
            "artifact_count": 5,
            "pending_count": 1,
            "ready_count": 2,
            "blocked_count": 2,
        },
        "evidence": {
            "fixture_vault_persisted": False,
            "screenshots": [
                {
                    "viewport": "desktop",
                    "path": "07_LOGS/Studio-Visual-QA/test/desktop.png",
                    "bytes": 100,
                    "not_blank": True,
                    "source_group_visible": True,
                    "missing_lifecycle_tokens": [],
                },
                {
                    "viewport": "mobile",
                    "path": "07_LOGS/Studio-Visual-QA/test/mobile.png",
                    "bytes": 80,
                    "not_blank": True,
                    "source_group_visible": True,
                    "missing_lifecycle_tokens": [],
                },
            ],
        },
    }
    _write(vault / VISUAL_QA_REPORT_RELATIVE_PATH, json.dumps(report, indent=2) + "\n")
    _write(vault / "07_LOGS/Studio-Visual-QA/test/desktop.png", "desktop")
    _write(vault / "07_LOGS/Studio-Visual-QA/test/mobile.png", "mobile")
    marketplace_bridge_report = {
        "ok": True,
        "status": "COMPLETE / MARKETPLACE PUBLISH AND INSTALL STUDIO UI VISUAL QA VERIFIED",
        "summary": {
            "marketplace_section_visible": True,
            "bridge_api_tokens_visible": True,
            "bridge_written_state_visible": True,
            "desktop_and_mobile_checked": True,
        },
        "fixture_evidence": {
            "sandbox_approval_request_written": True,
            "sandbox_approval_artifact_path": "07_LOGS/Agent-Activity/_forge_sandbox_approvals/forge-test.json",
            "marketplace_import_approval_status": "approved",
            "marketplace_import_approval_consumed": False,
            "sandbox_approval_consumed": False,
            "registry_written": False,
            "extension_files_written": [],
            "exact_once_marker_reserved": False,
        },
        "missing_required_tokens": [],
        "console_errors_or_warnings": [],
        "page_errors": [],
        "screenshots": [
            {
                "viewport": "desktop",
                "path": "07_LOGS/Studio-Visual-QA/test/marketplace-desktop.png",
                "bytes": 120,
                "not_blank": True,
                "marketplace_section_visible": True,
                "bridge_api_tokens_visible": True,
                "bridge_written_state_visible": True,
                "missing_required_tokens": [],
            },
            {
                "viewport": "mobile",
                "path": "07_LOGS/Studio-Visual-QA/test/marketplace-mobile.png",
                "bytes": 90,
                "not_blank": True,
                "marketplace_section_visible": True,
                "bridge_api_tokens_visible": True,
                "bridge_written_state_visible": True,
                "missing_required_tokens": [],
            },
        ],
    }
    _write(
        vault / MARKETPLACE_BRIDGE_VISUAL_QA_FALLBACK_REPORT_RELATIVE_PATH,
        json.dumps(marketplace_bridge_report, indent=2) + "\n",
    )
    _write(vault / "07_LOGS/Studio-Visual-QA/test/marketplace-desktop.png", "desktop")
    _write(vault / "07_LOGS/Studio-Visual-QA/test/marketplace-mobile.png", "mobile")
    live_control_report = {
        "ok": True,
        "status": "COMPLETE / MARKETPLACE LIVE STUDIO CONTROL PROOF VERIFIED",
        "fixture_policy": {
            "lifecycle_cleanup_completed": True,
            "marketplace_cleanup_completed": True,
        },
        "lifecycle_controls": {
            "checks": {
                "sandbox_wrong_digest_blocked": True,
                "sandbox_decision_recorded": True,
                "sandbox_ready_without_write": True,
                "sandbox_registry_written": True,
                "sandbox_approval_consumed": True,
                "live_wrong_digest_blocked": True,
                "live_decision_recorded": True,
                "live_ready_without_write": True,
                "live_install_executed": True,
                "live_approval_consumed": True,
                "rollback_wrong_digest_blocked": True,
                "rollback_decision_recorded": True,
                "rollback_ready_without_write": True,
                "rollback_executed": True,
                "rollback_approval_consumed": True,
                "registry_returned_to_sandbox": True,
                "extension_files_retained_after_rollback": True,
                "protected_core_mutation_blocked": True,
            }
        },
        "marketplace_controls": {
            "marketplace_publish": {
                "catalog_listing_written": True,
                "catalog_entry_count": 1,
            },
            "sandbox_request_bridge": {
                "marketplace_import_approval_consumed": False,
                "registry_written": False,
                "extension_files_written": [],
                "exact_once_marker_reserved": False,
            },
            "marketplace_install": {
                "marketplace_install_executed": True,
                "marketplace_import_approval_consumed": True,
                "sandbox_approval_consumed": True,
                "registry_written": True,
                "extension_files_written": ["extensions/ugc-campaign-studio/manifest.install.json"],
                "exact_once_marker_reserved": True,
            },
            "checks": {
                "package_wrong_digest_blocked": True,
                "package_artifact_written": True,
                "import_preview_ok": True,
                "import_preview_no_install": True,
                "catalog_initially_readable": True,
                "publish_preview_ok": True,
                "publish_wrong_digest_blocked": True,
                "catalog_listing_written": True,
                "catalog_entry_readable": True,
                "import_approval_wrong_digest_blocked": True,
                "import_approval_written": True,
                "import_decision_recorded": True,
                "bridge_preview_ok": True,
                "bridge_wrong_digest_blocked": True,
                "sandbox_request_written": True,
                "sandbox_decision_recorded": True,
                "marketplace_install_ready_without_write": True,
                "marketplace_install_executed": True,
                "marketplace_import_approval_consumed_by_install": True,
                "sandbox_approval_consumed_by_install": True,
                "registry_written_by_marketplace_install": True,
                "extension_files_written_by_marketplace_install": True,
                "exact_once_marker_reserved_by_marketplace_install": True,
                "duplicate_marketplace_install_blocked": True,
            },
        },
        "authority": {
            "real_vault_forge_approval_write_allowed": False,
            "real_vault_registry_write_allowed": False,
            "real_vault_extension_file_write_allowed": False,
            "real_vault_exact_once_marker_write_allowed": False,
            "provider_or_model_call_allowed": False,
            "agent_bus_dispatch_allowed": False,
            "protected_core_mutation_allowed": False,
            "pulse_memory_mutation_allowed": False,
            "personal_map_mutation_allowed": False,
            "rnd_truth_state_mutation_allowed": False,
            "canonical_mutation_allowed": False,
        },
    }
    _write(vault / LIVE_STUDIO_CONTROL_PROOF_FALLBACK_REPORT_RELATIVE_PATH, json.dumps(live_control_report, indent=2) + "\n")
    operator_use_report = {
        "ok": True,
        "status": "COMPLETE / MARKETPLACE OPERATOR USE STUDIO BUTTON FLOW VERIFIED",
        "summary": {
            "page_identity_ok": True,
            "publish_button_clicked": True,
            "install_button_clicked": True,
            "publish_status_visible_after_refresh": True,
            "install_status_visible_after_refresh": True,
            "operator_confirmations_accepted": 2,
            "required_api_methods_called": True,
            "desktop_and_mobile_checked": True,
            "screenshots_not_blank": True,
            "marketplace_section_visible": True,
            "fixture_registry_written": True,
            "fixture_extension_files_written": True,
            "fixture_import_approval_consumed": True,
            "fixture_sandbox_approval_consumed": True,
            "fixture_exact_once_marker_written": True,
            "fixture_cleanup_completed": True,
        },
        "missing_required_api_methods": [],
        "console_errors_or_warnings": [],
        "page_errors": [],
        "authority": {
            "real_vault_approval_artifact_write_allowed": False,
            "real_vault_registry_write_allowed": False,
            "real_vault_extension_file_write_allowed": False,
            "real_vault_exact_once_marker_write_allowed": False,
            "remote_marketplace_call_allowed": False,
            "third_party_package_exchange_allowed": False,
            "unauthorized_auto_install_allowed": False,
            "generic_approval_center_write_control_allowed": False,
            "provider_or_model_call_allowed": False,
            "agent_bus_dispatch_allowed": False,
            "protected_core_mutation_allowed": False,
            "pulse_memory_mutation_allowed": False,
            "personal_map_mutation_allowed": False,
            "rnd_truth_state_mutation_allowed": False,
            "canonical_mutation_allowed": False,
        },
        "screenshots": [
            {
                "step": "after-publish",
                "viewport": "desktop",
                "path": "07_LOGS/Studio-Visual-QA/test/operator-publish.png",
                "bytes": 120,
                "not_blank": True,
                "marketplace_section_visible": True,
                "framework_overlay_detected": False,
                "status_text": "Published forge-listing",
                "status_state": "complete",
            },
            {
                "step": "after-install",
                "viewport": "desktop",
                "path": "07_LOGS/Studio-Visual-QA/test/operator-install.png",
                "bytes": 120,
                "not_blank": True,
                "marketplace_section_visible": True,
                "framework_overlay_detected": False,
                "status_text": "Marketplace install complete",
                "status_state": "complete",
            },
            {
                "step": "after-install",
                "viewport": "mobile",
                "path": "07_LOGS/Studio-Visual-QA/test/operator-mobile.png",
                "bytes": 90,
                "not_blank": True,
                "marketplace_section_visible": True,
                "framework_overlay_detected": False,
                "status_text": "Marketplace install complete",
                "status_state": "complete",
            },
        ],
    }
    _write(vault / OPERATOR_USE_STUDIO_PROOF_REPORT_RELATIVE_PATH, json.dumps(operator_use_report, indent=2) + "\n")
    closeout_smoke_report_path = Path(
        "07_LOGS/Studio-Visual-QA/2026-05-22-chaser-forge-marketplace-operator-use-closeout-smoke/"
        "chaser-forge-marketplace-operator-use-visual-qa-report.json"
    )
    _write(vault / closeout_smoke_report_path, json.dumps(operator_use_report, indent=2) + "\n")
    _write(
        vault / OPERATOR_USE_CLOSEOUT_SMOKE_RESULT_RELATIVE_PATH,
        json.dumps(
            {
                "ok": True,
                "status": "COMPLETE / DIRECT CLOSEOUT SMOKE VERIFIED",
                "elapsed_seconds": 0.02,
                "checks": {
                    "report_ok": True,
                    "publish_status_visible_after_refresh": True,
                    "install_status_visible_after_refresh": True,
                    "required_api_methods_called": True,
                    "fixture_registry_written": True,
                    "fixture_exact_once_marker_written": True,
                    "report_written": True,
                },
                "failures": [],
                "report_path": closeout_smoke_report_path.as_posix(),
            },
            indent=2,
        )
        + "\n",
    )
    _write(
        vault / LOCAL_MARKETPLACE_LIBRARY_SMOKE_RESULT_RELATIVE_PATH,
        json.dumps(
            {
                "ok": True,
                "status": "COMPLETE / LOCAL MARKETPLACE LIBRARY STUDIO USE VERIFIED",
                "elapsed_seconds": 0.03,
                "checks": {
                    "library_before_listed_not_installed": True,
                    "library_after_ok": True,
                    "library_after_has_one_item": True,
                    "library_after_listed_installed": True,
                    "library_item_installed": True,
                    "library_item_registry_status_visible": True,
                    "library_item_target_paths_verified": True,
                    "panel_summary_library_ready": True,
                    "panel_summary_library_read_only": True,
                    "panel_registry_api_wired": True,
                    "panel_registry_readiness_wired": True,
                    "frontend_library_section_wired": True,
                    "frontend_library_api_token_wired": True,
                    "remote_exchange_blocked": True,
                    "unauthorized_auto_install_blocked": True,
                    "real_vault_registry_and_catalog_unchanged": True,
                    "fixture_cleanup_completed": True,
                },
                "flow_summary": {
                    "library_item_count": 1,
                    "listed_installed_count": 1,
                    "installed_unlisted_count": 0,
                    "marketplace_install_executed": True,
                    "registry_written_in_fixture": True,
                },
                "failures": [],
            },
            indent=2,
        )
        + "\n",
    )
    _write(
        vault / REMOTE_DISTRIBUTION_SMOKE_RESULT_RELATIVE_PATH,
        json.dumps(
            {
                "ok": True,
                "status": "COMPLETE / GOVERNED REMOTE DISTRIBUTION FOUNDATION VERIFIED",
                "elapsed_seconds": 0.04,
                "checks": {
                    "remote_preview_ready": True,
                    "wrong_index_digest_blocked": True,
                    "remote_index_written": True,
                    "remote_network_publish_blocked": True,
                    "remote_payment_mutation_blocked": True,
                    "remote_license_checkout_blocked": True,
                    "ingest_preview_trusted": True,
                    "ingest_preview_attestation_verified": True,
                    "wrong_ingest_statement_blocked": True,
                    "remote_listing_ingested": True,
                    "catalog_entry_written": True,
                    "library_remote_item_visible": True,
                    "library_item_not_installed": True,
                    "panel_summary_remote_ready": True,
                    "panel_summary_remote_ingest_ready": True,
                    "panel_registry_remote_methods_wired": True,
                    "panel_registry_remote_readiness_wired": True,
                    "frontend_remote_section_wired": True,
                    "frontend_remote_api_tokens_wired": True,
                    "real_vault_registry_catalog_remote_index_unchanged": True,
                    "fixture_cleanup_completed": True,
                },
                "flow_summary": {
                    "remote_index_digest_sha256": "abc",
                    "listing_digest_sha256": "def",
                    "ingested_listing_id": "forge-remote-listing-test",
                    "catalog_entry_count": 1,
                    "library_item_count": 1,
                },
                "failures": [],
            },
            indent=2,
        )
        + "\n",
    )
    _write(
        vault / HOSTED_MARKETPLACE_EXPORT_BUNDLE_SMOKE_RESULT_RELATIVE_PATH,
        json.dumps(
            {
                "ok": True,
                "status": "COMPLETE / GOVERNED HOSTED MARKETPLACE EXPORT BUNDLE VERIFIED",
                "elapsed_seconds": 0.03,
                "checks": {
                    "hosted_preview_ready": True,
                    "wrong_bundle_digest_blocked": True,
                    "wrong_remote_index_digest_blocked": True,
                    "hosted_bundle_written": True,
                    "manual_static_host_ready": True,
                    "hosted_bundle_publication_manifest_ready": True,
                    "hosted_bundle_no_credentials": True,
                    "hosted_bundle_network_publish_blocked": True,
                    "hosted_bundle_payment_mutation_blocked": True,
                    "hosted_bundle_license_checkout_blocked": True,
                    "hosted_bundle_package_install_blocked": True,
                    "panel_summary_hosted_ready": True,
                    "panel_summary_hosted_manual_static_ready": True,
                    "panel_registry_hosted_methods_wired": True,
                    "panel_registry_hosted_readiness_wired": True,
                    "frontend_hosted_section_wired": True,
                    "frontend_hosted_api_tokens_wired": True,
                    "real_vault_registry_catalog_remote_index_hosted_bundle_unchanged": True,
                    "fixture_cleanup_completed": True,
                },
                "flow_summary": {
                    "remote_index_digest_sha256": "abc",
                    "hosted_bundle_digest_sha256": "bundle",
                    "hosted_bundle_artifact_path": "07_LOGS/Workflow-Proofs/Forge-Marketplace-Hosted-Bundles/test.json",
                    "entry_count": 1,
                    "publication_mode": "manual_static_host",
                },
                "failures": [],
            },
            indent=2,
        )
        + "\n",
    )
    _write(
        vault / STATIC_HOST_PUBLICATION_SMOKE_RESULT_RELATIVE_PATH,
        json.dumps(
            {
                "ok": True,
                "status": "COMPLETE / GOVERNED STATIC HOST PUBLICATION PROOF VERIFIED",
                "elapsed_seconds": 0.03,
                "checks": {
                    "static_publication_preview_ready": True,
                    "wrong_static_publication_digest_blocked": True,
                    "wrong_hosted_bundle_digest_blocked": True,
                    "wrong_remote_index_digest_blocked": True,
                    "static_publication_written": True,
                    "static_publication_files_ready": True,
                    "manual_upload_ready": True,
                    "network_upload_blocked": True,
                    "external_registry_mutation_blocked": True,
                    "payment_mutation_blocked": True,
                    "license_checkout_blocked": True,
                    "package_install_blocked": True,
                    "panel_summary_static_ready": True,
                    "panel_summary_static_manual_upload_ready": True,
                    "panel_registry_static_methods_wired": True,
                    "panel_registry_static_readiness_wired": True,
                    "frontend_static_section_wired": True,
                    "frontend_static_api_tokens_wired": True,
                    "real_vault_registry_catalog_remote_index_hosted_bundle_static_publication_unchanged": True,
                    "fixture_cleanup_completed": True,
                },
                "flow_summary": {
                    "remote_index_digest_sha256": "abc",
                    "hosted_bundle_digest_sha256": "bundle",
                    "static_publication_digest_sha256": "static",
                    "static_publication_dir_path": "07_LOGS/Workflow-Proofs/Forge-Marketplace-Static-Host-Publications/test",
                    "file_count": 5,
                },
                "failures": [],
            },
            indent=2,
        )
        + "\n",
    )
    _write(
        vault / STATIC_UPLOAD_HANDOFF_SMOKE_RESULT_RELATIVE_PATH,
        json.dumps(
            {
                "ok": True,
                "status": "COMPLETE / GOVERNED STATIC HOST UPLOAD HANDOFF VERIFIED",
                "elapsed_seconds": 0.03,
                "checks": {
                    "upload_handoff_preview_ready": True,
                    "wrong_upload_handoff_digest_blocked": True,
                    "wrong_static_publication_digest_blocked": True,
                    "upload_handoff_written": True,
                    "upload_handoff_files_written": True,
                    "static_publication_files_present": True,
                    "manual_upload_handoff_ready": True,
                    "network_upload_blocked": True,
                    "external_registry_mutation_blocked": True,
                    "payment_mutation_blocked": True,
                    "license_checkout_blocked": True,
                    "package_install_blocked": True,
                    "panel_summary_upload_handoff_ready": True,
                    "panel_registry_upload_handoff_methods_wired": True,
                    "panel_registry_upload_handoff_readiness_wired": True,
                    "frontend_upload_handoff_section_wired": True,
                    "frontend_upload_handoff_api_tokens_wired": True,
                    "real_vault_registry_catalog_remote_index_hosted_bundle_static_publication_upload_handoff_unchanged": True,
                    "fixture_cleanup_completed": True,
                },
                "flow_summary": {
                    "remote_index_digest_sha256": "abc",
                    "hosted_bundle_digest_sha256": "bundle",
                    "static_publication_digest_sha256": "static",
                    "upload_handoff_digest_sha256": "handoff",
                    "upload_handoff_json_path": "07_LOGS/Workflow-Proofs/Forge-Marketplace-Static-Host-Upload-Handoffs/test.json",
                    "upload_handoff_markdown_path": "07_LOGS/Workflow-Proofs/Forge-Marketplace-Static-Host-Upload-Handoffs/test.md",
                    "file_count": 5,
                },
                "failures": [],
            },
            indent=2,
        )
        + "\n",
    )
    _write(
        vault / STATIC_UPLOAD_RECEIPT_SMOKE_RESULT_RELATIVE_PATH,
        json.dumps(
            {
                "ok": True,
                "status": "COMPLETE / GOVERNED STATIC HOST UPLOAD RECEIPT VERIFIED",
                "elapsed_seconds": 0.03,
                "checks": {
                    "upload_receipt_preview_ready": True,
                    "wrong_upload_receipt_digest_blocked": True,
                    "wrong_operator_receipt_statement_blocked": True,
                    "wrong_upload_handoff_digest_blocked": True,
                    "upload_receipt_written": True,
                    "upload_receipt_files_written": True,
                    "operator_receipt_statement_recorded": True,
                    "operator_manual_upload_claim_recorded": True,
                    "network_fetch_blocked": True,
                    "network_upload_blocked": True,
                    "external_registry_mutation_blocked": True,
                    "payment_mutation_blocked": True,
                    "license_checkout_blocked": True,
                    "package_install_blocked": True,
                    "panel_summary_upload_receipt_ready": True,
                    "panel_registry_upload_receipt_methods_wired": True,
                    "panel_registry_upload_receipt_readiness_wired": True,
                    "frontend_upload_receipt_section_wired": True,
                    "frontend_upload_receipt_api_tokens_wired": True,
                    "real_vault_registry_catalog_remote_index_hosted_bundle_static_publication_upload_handoff_upload_receipt_unchanged": True,
                    "fixture_cleanup_completed": True,
                },
                "flow_summary": {
                    "remote_index_digest_sha256": "abc",
                    "hosted_bundle_digest_sha256": "bundle",
                    "static_publication_digest_sha256": "static",
                    "upload_handoff_digest_sha256": "handoff",
                    "upload_receipt_digest_sha256": "receipt",
                    "upload_receipt_json_path": "07_LOGS/Workflow-Proofs/Forge-Marketplace-Static-Host-Upload-Receipts/test.json",
                    "upload_receipt_markdown_path": "07_LOGS/Workflow-Proofs/Forge-Marketplace-Static-Host-Upload-Receipts/test.md",
                    "operator_uploaded_base_url": "https://example.invalid/chaser-forge",
                    "file_count": 5,
                },
                "failures": [],
            },
            indent=2,
        )
        + "\n",
    )
    _write(
        vault / PUBLISHED_STATIC_INDEX_REGISTRATION_SMOKE_RESULT_RELATIVE_PATH,
        json.dumps(
            {
                "ok": True,
                "status": "COMPLETE / GOVERNED PUBLISHED STATIC INDEX REGISTRATION VERIFIED",
                "elapsed_seconds": 0.03,
                "checks": {
                    "published_static_index_registration_preview_ready": True,
                    "wrong_published_static_index_registration_digest_blocked": True,
                    "wrong_operator_registration_statement_blocked": True,
                    "wrong_upload_receipt_digest_blocked": True,
                    "published_static_index_registration_written": True,
                    "published_static_index_registration_files_written": True,
                    "operator_registration_statement_recorded": True,
                    "operator_declared_published_index_registered": True,
                    "live_url_fetch_unverified_and_blocked": True,
                    "network_upload_blocked": True,
                    "external_registry_mutation_blocked": True,
                    "payment_mutation_blocked": True,
                    "license_checkout_blocked": True,
                    "package_install_blocked": True,
                    "panel_summary_published_static_index_registration_ready": True,
                    "panel_registry_published_static_index_registration_methods_wired": True,
                    "panel_registry_published_static_index_registration_readiness_wired": True,
                    "frontend_published_static_index_registration_section_wired": True,
                    "frontend_published_static_index_registration_api_tokens_wired": True,
                    "real_vault_registry_catalog_distribution_registration_paths_unchanged": True,
                    "fixture_cleanup_completed": True,
                },
                "flow_summary": {
                    "remote_index_digest_sha256": "abc",
                    "hosted_bundle_digest_sha256": "bundle",
                    "static_publication_digest_sha256": "static",
                    "upload_handoff_digest_sha256": "handoff",
                    "upload_receipt_digest_sha256": "receipt",
                    "published_static_index_registration_digest_sha256": "registration",
                    "published_static_index_registration_json_path": "07_LOGS/Workflow-Proofs/Forge-Marketplace-Published-Static-Index-Registrations/test.json",
                    "published_static_index_registration_markdown_path": "07_LOGS/Workflow-Proofs/Forge-Marketplace-Published-Static-Index-Registrations/test.md",
                    "operator_published_static_index_url": "https://example.invalid/chaser-forge/index.json",
                    "file_count": 5,
                },
                "failures": [],
            },
            indent=2,
        )
        + "\n",
    )
    _write(vault / "07_LOGS/Studio-Visual-QA/test/operator-publish.png", "desktop")
    _write(vault / "07_LOGS/Studio-Visual-QA/test/operator-install.png", "desktop")
    _write(vault / "07_LOGS/Studio-Visual-QA/test/operator-mobile.png", "mobile")


def test_chaser_forge_panel_model_is_mvp_ready(tmp_path: Path) -> None:
    panel = build_chaser_forge_panel(tmp_path)

    assert panel["surface"] == "chaser_forge_panel"
    assert panel["status"] == "mvp_foundation_ready"
    assert panel["authority"]["local_catalog_write_allowed"] is True
    assert panel["authority"]["governed_extension_owned_file_write_allowed"] is True
    assert panel["authority"]["ambient_remote_marketplace_calls_allowed"] is False
    assert panel["authority"]["network_upload_allowed"] is False
    assert panel["authority"]["network_fetch_allowed"] is False
    assert panel["authority"]["payment_mutation_allowed"] is False
    assert panel["authority"]["provider_calls_allowed"] is False
    assert panel["authority"]["agent_bus_dispatch_allowed"] is False
    assert panel["authority"]["protected_core_mutation_allowed"] is False
    assert panel["operating_context"]["title"] == "Extension Operating Context"
    assert len(panel["operating_context"]["cards"]) == 4
    assert panel["readiness"]["rows"][0]["label"] == "Manifest validation and extension-point policy"
    coverage = {row["capability"] for row in panel["feature_family_coverage"]}
    assert "Approved extension points, manifest validation, protected-core guard" in coverage
    assert "Local catalog, local library, marketplace import/install lifecycle" in coverage
    assert "Remote index, hosted export bundle, static publication, upload handoff, upload receipt, published index registration" in coverage
    product_objects = {item["id"] for item in panel["product_objects"]}
    assert {"forge-foundation", "local-library", "governed-install", "static-distribution", "proof-chain", "blocked-authority"} <= product_objects
    assert panel["summary"]["demo_manifest_valid"] is True
    assert panel["summary"]["local_mvp_implemented"] is False
    assert panel["summary"]["local_mvp_completion_status"] == "PARTIAL / LOCAL MVP EVIDENCE CHAIN NOT YET CLOSED"
    assert panel["summary"]["live_studio_control_proof_verified"] is False
    assert panel["summary"]["operator_use_studio_proof_verified"] is False
    assert panel["summary"]["public_marketplace_deferred"] is False
    assert panel["summary"]["public_marketplace_status"] == "COMPLETE LOCALLY / LIVE INDEX INPUT REQUIRED"
    assert panel["summary"]["generated_core_mutation_allowed"] is False
    assert panel["summary"]["installer_writes_enabled"] is False
    assert panel["summary"]["sandbox_install_model_declared"] is True
    assert panel["summary"]["sandbox_approval_preview_ready"] is True
    assert panel["summary"]["sandbox_approval_request_written"] is False
    assert panel["summary"]["sandbox_registry_writer_built"] is True
    assert panel["summary"]["sandbox_registry_writer_ready"] is False
    assert panel["summary"]["registry_writer_built"] is True
    assert panel["summary"]["live_install_approval_packet_built"] is True
    assert panel["summary"]["live_install_approval_preview_ready"] is False
    assert panel["summary"]["live_install_executor_built"] is True
    assert panel["summary"]["live_install_executor_ready"] is False
    assert panel["summary"]["rollback_approval_packet_built"] is True
    assert panel["summary"]["rollback_approval_preview_ready"] is False
    assert panel["summary"]["rollback_executor_built"] is True
    assert panel["summary"]["rollback_executor_ready"] is False
    assert panel["summary"]["approval_center_decision_handoff_built"] is True
    assert panel["summary"]["operator_decision_form_contract_built"] is True
    assert panel["summary"]["operator_decision_form_write_enabled"] is False
    assert panel["summary"]["operator_decision_form_generic_control"] is False
    assert panel["summary"]["approval_decision_write_enabled_by_panel"] is False
    assert panel["summary"]["approval_decision_consumption_allowed"] is False
    assert panel["summary"]["decision_bound_executor_validation_ready"] is True
    assert panel["summary"]["executor_requires_decision_sidecar"] is True
    assert panel["summary"]["proof_deck_log_only"] is True
    assert panel["summary"]["proof_deck_write_executed"] is False
    assert panel["summary"]["proof_deck_read_only"] is True
    assert panel["summary"]["marketplace_export_package_built"] is True
    assert panel["summary"]["marketplace_export_preview_ready"] is True
    assert panel["summary"]["marketplace_package_write_enabled_by_panel"] is True
    assert panel["summary"]["marketplace_catalog_built"] is True
    assert panel["summary"]["marketplace_catalog_ready"] is True
    assert panel["summary"]["marketplace_local_library_built"] is True
    assert panel["summary"]["marketplace_local_library_ready"] is True
    assert panel["summary"]["marketplace_local_library_read_only"] is True
    assert panel["summary"]["marketplace_local_library_item_count"] == 0
    assert panel["summary"]["marketplace_local_library_remote_exchange_blocked"] is True
    assert panel["summary"]["marketplace_remote_distribution_built"] is True
    assert panel["summary"]["marketplace_remote_distribution_ready"] is True
    assert panel["summary"]["marketplace_remote_index_write_digest_gated"] is True
    assert panel["summary"]["marketplace_remote_ingest_preview_ready"] is True
    assert panel["summary"]["marketplace_remote_ingest_digest_gated"] is True
    assert panel["summary"]["marketplace_remote_network_calls_blocked"] is True
    assert panel["summary"]["marketplace_remote_payment_mutation_blocked"] is True
    assert panel["summary"]["marketplace_remote_publisher_attestation_verified"] is True
    assert panel["summary"]["marketplace_hosted_export_bundle_built"] is True
    assert panel["summary"]["marketplace_hosted_export_bundle_ready"] is True
    assert panel["summary"]["marketplace_hosted_export_bundle_digest_gated"] is True
    assert panel["summary"]["marketplace_hosted_export_manual_static_ready"] is True
    assert panel["summary"]["marketplace_hosted_export_network_publish_blocked"] is True
    assert panel["summary"]["marketplace_hosted_export_payment_mutation_blocked"] is True
    assert panel["summary"]["marketplace_static_host_publication_built"] is True
    assert panel["summary"]["marketplace_static_host_publication_ready"] is True
    assert panel["summary"]["marketplace_static_host_publication_digest_gated"] is True
    assert panel["summary"]["marketplace_static_host_publication_manual_upload_ready"] is True
    assert panel["summary"]["marketplace_static_host_publication_network_upload_blocked"] is True
    assert panel["summary"]["marketplace_static_host_publication_payment_mutation_blocked"] is True
    assert panel["summary"]["marketplace_static_upload_handoff_built"] is True
    assert panel["summary"]["marketplace_static_upload_handoff_ready"] is True
    assert panel["summary"]["marketplace_static_upload_handoff_digest_gated"] is True
    assert panel["summary"]["marketplace_static_upload_handoff_manual_action_required"] is True
    assert panel["summary"]["marketplace_static_upload_handoff_network_upload_blocked"] is True
    assert panel["summary"]["marketplace_static_upload_handoff_external_registry_blocked"] is True
    assert panel["summary"]["marketplace_static_upload_receipt_built"] is True
    assert panel["summary"]["marketplace_static_upload_receipt_ready"] is True
    assert panel["summary"]["marketplace_static_upload_receipt_digest_gated"] is True
    assert panel["summary"]["marketplace_static_upload_receipt_operator_statement_required"] is True
    assert panel["summary"]["marketplace_static_upload_receipt_network_fetch_blocked"] is True
    assert panel["summary"]["marketplace_static_upload_receipt_external_registry_blocked"] is True
    assert panel["summary"]["marketplace_published_static_index_registration_built"] is True
    assert panel["summary"]["marketplace_published_static_index_registration_ready"] is True
    assert panel["summary"]["marketplace_published_static_index_registration_digest_gated"] is True
    assert panel["summary"]["marketplace_published_static_index_registration_operator_statement_required"] is True
    assert panel["summary"]["marketplace_published_static_index_registration_network_fetch_blocked"] is True
    assert panel["summary"]["marketplace_published_static_index_registration_external_registry_blocked"] is True
    assert panel["summary"]["marketplace_published_static_index_registration_live_url_unverified"] is True
    assert panel["summary"]["marketplace_publish_built"] is True
    assert panel["summary"]["marketplace_publish_preview_ready"] is True
    assert panel["summary"]["marketplace_publish_allowed"] is True
    assert panel["summary"]["marketplace_publish_write_enabled_by_panel"] is True
    assert panel["summary"]["marketplace_import_preview_built"] is True
    assert panel["summary"]["marketplace_import_preview_ready"] is True
    assert panel["summary"]["marketplace_import_approval_packet_built"] is True
    assert panel["summary"]["marketplace_import_approval_preview_ready"] is True
    assert panel["summary"]["marketplace_import_approval_request_written"] is False
    assert panel["summary"]["marketplace_import_approval_consumption_allowed"] is True
    assert panel["summary"]["marketplace_import_approval_consumption_requires_install_executor"] is True
    assert panel["summary"]["marketplace_import_sandbox_request_bridge_built"] is True
    assert panel["summary"]["marketplace_import_sandbox_request_preview_ready"] is False
    assert panel["summary"]["marketplace_import_sandbox_request_written"] is False
    assert panel["summary"]["marketplace_import_approval_consumed_by_bridge"] is False
    assert panel["summary"]["marketplace_import_sandbox_execution_allowed"] is True
    assert panel["summary"]["marketplace_install_executor_built"] is True
    assert panel["summary"]["marketplace_governed_auto_install_available"] is True
    assert panel["summary"]["marketplace_auto_install_allowed"] is True
    assert panel["summary"]["marketplace_auto_install_requires_approval"] is True
    assert panel["summary"]["marketplace_unauthorized_auto_install_allowed"] is False
    assert panel["demo_manifest"]["validation"]["valid"] is True
    assert panel["registry"]["surface"] == "chaser_forge_extension_registry"
    assert panel["sandbox_approval"]["surface"] == "chaser_forge_sandbox_install_approval"
    assert panel["sandbox_registry_writer"]["surface"] == "chaser_forge_sandbox_registry_writer"
    assert panel["live_install_approval"]["surface"] == "chaser_forge_live_install_approval"
    assert panel["live_install_executor"]["surface"] == "chaser_forge_live_install_executor"
    assert panel["rollback_approval"]["surface"] == "chaser_forge_rollback_approval"
    assert panel["rollback_executor"]["surface"] == "chaser_forge_rollback_executor"
    assert panel["approval_decision_handoff"]["surface"] == "chaser_forge_approval_center_decision_handoff"
    assert panel["approval_decision_handoff"]["api_method"] == "review_chaser_forge_approval_decision"
    assert panel["approval_decision_handoff"]["source_specific"] is True
    assert panel["approval_decision_handoff"]["approval_consumption_allowed"] is False
    assert panel["approval_decision_handoff"]["forge_execution_allowed"] is False
    assert panel["approval_decision_handoff"]["executor_consumption_bound_to_decision_sidecar"] is True
    assert panel["approval_decision_handoff"]["decision_record_digest_required_by_executor"] is True
    assert panel["approval_decision_form"]["surface"] == "chaser_forge_operator_decision_form"
    assert panel["approval_decision_form"]["api_method"] == "get_chaser_forge_approval_decision_form"
    assert panel["approval_decision_form"]["submit_api_method"] == "review_chaser_forge_approval_decision"
    assert panel["approval_decision_form"]["source_specific"] is True
    assert panel["approval_decision_form"]["generic_approval_center_control"] is False
    assert panel["approval_decision_form"]["prepares_copyable_operator_statement"] is True
    assert panel["approval_decision_form"]["prepares_submit_payload"] is True
    assert panel["approval_decision_form"]["write_enabled_by_form_preview"] is False
    assert panel["approval_decision_form"]["approval_consumption_allowed"] is False
    assert panel["approval_decision_form"]["forge_execution_allowed"] is False
    assert panel["proof_deck"]["surface"] == "chaser_forge_proof_deck"
    assert panel["proof_deck"]["write_executed"] is False
    assert panel["marketplace"]["surface"] == "chaser_forge_marketplace_import_export_foundation"
    assert panel["marketplace"]["export_api_method"] == "get_chaser_forge_marketplace_export_package"
    assert panel["marketplace"]["write_api_method"] == "write_chaser_forge_marketplace_export_package"
    assert panel["marketplace"]["import_api_method"] == "get_chaser_forge_marketplace_import_preview"
    assert panel["marketplace"]["import_approval_api_method"] == "request_chaser_forge_marketplace_import_sandbox_approval"
    assert panel["marketplace"]["import_sandbox_request_preview_api_method"] == (
        "get_chaser_forge_marketplace_import_sandbox_request"
    )
    assert panel["marketplace"]["import_sandbox_request_api_method"] == (
        "request_chaser_forge_marketplace_import_sandbox_request"
    )
    assert panel["marketplace"]["catalog_api_method"] == "get_chaser_forge_marketplace_catalog"
    assert panel["marketplace"]["local_library_api_method"] == "get_chaser_forge_marketplace_local_library"
    assert panel["marketplace"]["remote_distribution_api_method"] == "get_chaser_forge_marketplace_remote_distribution"
    assert panel["marketplace"]["remote_index_write_api_method"] == "write_chaser_forge_marketplace_remote_index"
    assert panel["marketplace"]["remote_ingest_api_method"] == "ingest_chaser_forge_marketplace_remote_listing"
    assert panel["marketplace"]["hosted_export_bundle_api_method"] == "get_chaser_forge_marketplace_hosted_export_bundle"
    assert panel["marketplace"]["hosted_export_bundle_write_api_method"] == "write_chaser_forge_marketplace_hosted_export_bundle"
    assert panel["marketplace"]["static_host_publication_api_method"] == "get_chaser_forge_marketplace_static_host_publication"
    assert panel["marketplace"]["static_host_publication_write_api_method"] == "write_chaser_forge_marketplace_static_host_publication"
    assert panel["marketplace"]["static_upload_handoff_api_method"] == "get_chaser_forge_marketplace_static_host_upload_handoff"
    assert panel["marketplace"]["static_upload_handoff_write_api_method"] == "write_chaser_forge_marketplace_static_host_upload_handoff"
    assert panel["marketplace"]["static_upload_receipt_api_method"] == "get_chaser_forge_marketplace_static_host_upload_receipt"
    assert panel["marketplace"]["static_upload_receipt_write_api_method"] == "write_chaser_forge_marketplace_static_host_upload_receipt"
    assert panel["marketplace"]["published_static_index_registration_api_method"] == (
        "get_chaser_forge_marketplace_published_static_index_registration"
    )
    assert panel["marketplace"]["published_static_index_registration_write_api_method"] == (
        "write_chaser_forge_marketplace_published_static_index_registration"
    )
    assert panel["marketplace"]["local_library"]["ok"] is True
    assert panel["marketplace"]["local_library"]["authority"]["local_marketplace_library_read_only"] is True
    assert panel["marketplace"]["local_library"]["remote_marketplace_call_allowed"] is False
    assert panel["marketplace"]["publish_preview_api_method"] == "get_chaser_forge_marketplace_publish_preview"
    assert panel["marketplace"]["publish_api_method"] == "publish_chaser_forge_marketplace_package"
    assert panel["marketplace"]["install_api_method"] == "execute_chaser_forge_marketplace_install"
    assert panel["marketplace"]["write_enabled_by_panel"] is True
    assert panel["marketplace"]["publish_allowed"] is True
    assert panel["marketplace"]["auto_install_allowed"] is True
    assert panel["marketplace"]["auto_install_requires_approval"] is True
    assert panel["marketplace"]["remote_distribution"]["ok"] is True
    assert panel["marketplace"]["remote_distribution"]["remote_index_artifact_written"] is False
    assert panel["marketplace"]["remote_distribution"]["remote_network_publish_allowed"] is False
    assert panel["marketplace"]["remote_distribution"]["payment_mutation_allowed"] is False
    assert panel["marketplace"]["remote_ingest_preview"]["ok"] is True
    assert panel["marketplace"]["remote_ingest_preview"]["publisher_attestation_verified"] is True
    assert panel["marketplace"]["remote_ingest_preview"]["publisher_trusted"] is True
    assert panel["marketplace"]["hosted_export_bundle"]["ok"] is True
    assert panel["marketplace"]["hosted_export_bundle"]["hosted_bundle_artifact_written"] is False
    assert panel["marketplace"]["hosted_export_bundle"]["manual_static_host_ready"] is True
    assert panel["marketplace"]["hosted_export_bundle"]["remote_network_publish_allowed"] is False
    assert panel["marketplace"]["hosted_export_bundle"]["payment_mutation_allowed"] is False
    assert panel["marketplace"]["static_host_publication"]["ok"] is True
    assert panel["marketplace"]["static_host_publication"]["static_publication_written"] is False
    assert panel["marketplace"]["static_host_publication"]["manual_upload_ready"] is True
    assert panel["marketplace"]["static_host_publication"]["network_upload_performed"] is False
    assert panel["marketplace"]["static_host_publication"]["remote_network_publish_allowed"] is False
    assert panel["marketplace"]["static_host_publication"]["external_registry_mutation_allowed"] is False
    assert panel["marketplace"]["static_host_publication"]["payment_mutation_allowed"] is False
    assert panel["marketplace"]["static_upload_handoff"]["ok"] is True
    assert panel["marketplace"]["static_upload_handoff"]["upload_handoff_written"] is False
    assert panel["marketplace"]["static_upload_handoff"]["manual_upload_handoff_ready"] is True
    assert panel["marketplace"]["static_upload_handoff"]["network_upload_performed"] is False
    assert panel["marketplace"]["static_upload_handoff"]["network_upload_allowed"] is False
    assert panel["marketplace"]["static_upload_handoff"]["external_registry_mutation_allowed"] is False
    assert panel["marketplace"]["static_upload_handoff"]["payment_mutation_allowed"] is False
    assert panel["marketplace"]["static_upload_receipt"]["ok"] is True
    assert panel["marketplace"]["static_upload_receipt"]["upload_receipt_written"] is False
    assert panel["marketplace"]["static_upload_receipt"]["manual_upload_receipt_ready"] is True
    assert panel["marketplace"]["static_upload_receipt"]["required_operator_receipt_statement"]
    assert panel["marketplace"]["static_upload_receipt"]["network_fetch_performed"] is False
    assert panel["marketplace"]["static_upload_receipt"]["network_fetch_allowed"] is False
    assert panel["marketplace"]["static_upload_receipt"]["external_registry_mutation_allowed"] is False
    assert panel["marketplace"]["static_upload_receipt"]["payment_mutation_allowed"] is False
    assert panel["marketplace"]["published_static_index_registration"]["ok"] is True
    assert panel["marketplace"]["published_static_index_registration"]["published_static_index_registration_written"] is False
    assert panel["marketplace"]["published_static_index_registration"]["published_static_index_registration_ready"] is True
    assert panel["marketplace"]["published_static_index_registration"]["required_operator_registration_statement"]
    assert panel["marketplace"]["published_static_index_registration"]["live_url_verified"] is False
    assert panel["marketplace"]["published_static_index_registration"]["network_fetch_performed"] is False
    assert panel["marketplace"]["published_static_index_registration"]["network_fetch_allowed"] is False
    assert panel["marketplace"]["published_static_index_registration"]["external_registry_mutation_allowed"] is False
    assert panel["marketplace"]["published_static_index_registration"]["payment_mutation_allowed"] is False
    assert panel["marketplace"]["export_package"]["ok"] is True
    assert panel["marketplace"]["catalog"]["ok"] is True
    assert panel["marketplace"]["publish_preview"]["ok"] is True
    assert panel["marketplace"]["export_package"]["package_artifact_written"] is False
    assert panel["marketplace"]["import_preview"]["ok"] is True
    assert panel["marketplace"]["import_preview"]["import_install_allowed"] is False
    assert panel["marketplace"]["import_approval_request"]["ok"] is True
    assert panel["marketplace"]["import_approval_request"]["approval_request_written"] is False
    assert panel["marketplace"]["import_approval_request"]["package_install_allowed"] is False
    assert panel["marketplace"]["import_sandbox_request"]["ok"] is False
    assert panel["marketplace"]["import_sandbox_request"]["sandbox_approval_request_written"] is False
    assert panel["marketplace"]["import_sandbox_request"]["marketplace_import_approval_consumed"] is False
    assert all(value is False for value in panel["blocked_authority"].values())


def test_chaser_forge_panel_surfaces_packaged_proof_deck_without_writes(tmp_path: Path) -> None:
    _seed_proof_deck_evidence(tmp_path)

    panel = build_chaser_forge_panel(tmp_path)

    assert panel["summary"]["proof_deck_packaged"] is True
    assert panel["summary"]["local_mvp_implemented"] is True
    assert panel["summary"]["local_mvp_completion_status"] == "COMPLETE / LOCAL GOVERNED MVP VERIFIED"
    assert panel["summary"]["live_studio_control_proof_verified"] is True
    assert panel["summary"]["operator_use_studio_proof_verified"] is True
    assert panel["summary"]["remaining_local_mvp_open_loops"] == []
    assert panel["summary"]["public_marketplace_deferred"] is False
    assert panel["summary"]["proof_deck_read_only"] is True
    assert panel["summary"]["proof_deck_write_executed"] is False
    assert panel["summary"]["proof_deck_blocker_count"] == 0
    assert panel["proof_deck"]["ok"] is True
    assert panel["proof_deck"]["read_only"] is True
    assert panel["proof_deck"]["writes"] == []
    assert panel["proof_deck"]["markdown_path"] == "07_LOGS/Workflow-Proofs/2026-05-21_chaser-forge-marketplace-proof-deck.md"
    assert panel["proof_deck"]["json_path"] == "07_LOGS/Workflow-Proofs/2026-05-21_chaser-forge-marketplace-proof-deck.json"
    assert not (tmp_path / panel["proof_deck"]["markdown_path"]).exists()
    assert not (tmp_path / panel["proof_deck"]["json_path"]).exists()
    assert panel["proof_deck"]["authority"]["approval_decision_allowed"] is False
    assert panel["proof_deck"]["authority"]["forge_registry_mutation_allowed"] is False


def test_studio_api_exposes_chaser_forge_panel(tmp_path: Path) -> None:
    api = StudioAPI(tmp_path)

    response = api.get_chaser_forge_panel()

    assert response["ok"] is True
    assert response["surface"] == "chaser_forge_panel"
    assert response["data"]["summary"]["demo_manifest_valid"] is True
    assert response["data"]["summary"]["sandbox_approval_preview_ready"] is True
    assert response["data"]["summary"]["sandbox_registry_writer_built"] is True
    assert response["data"]["summary"]["live_install_approval_packet_built"] is True
    assert response["data"]["summary"]["live_install_executor_built"] is True
    assert response["data"]["summary"]["rollback_approval_packet_built"] is True
    assert response["data"]["summary"]["rollback_executor_built"] is True
    assert response["data"]["summary"]["approval_center_decision_handoff_built"] is True
    assert response["data"]["summary"]["operator_decision_form_contract_built"] is True
    assert response["data"]["summary"]["decision_bound_executor_validation_ready"] is True
    assert response["data"]["summary"]["executor_requires_decision_sidecar"] is True
    assert response["data"]["summary"]["proof_deck_read_only"] is True
    assert response["data"]["summary"]["marketplace_export_preview_ready"] is True
    assert response["data"]["summary"]["marketplace_import_preview_ready"] is True
    assert response["data"]["summary"]["marketplace_import_approval_preview_ready"] is True
    assert response["data"]["summary"]["marketplace_import_sandbox_request_bridge_built"] is True
    assert response["data"]["summary"]["marketplace_remote_distribution_ready"] is True
    assert response["data"]["summary"]["marketplace_remote_ingest_preview_ready"] is True
    assert response["data"]["summary"]["marketplace_hosted_export_bundle_ready"] is True
    assert response["data"]["proof_deck"]["write_executed"] is False
    assert response["data"]["marketplace"]["export_package"]["package_artifact_written"] is False


def test_studio_api_digest_gates_chaser_forge_marketplace_package_write_and_import_preview(tmp_path: Path) -> None:
    api = StudioAPI(tmp_path)

    preview = api.get_chaser_forge_marketplace_export_package()
    assert preview["ok"] is True
    assert preview["data"]["ok"] is True
    assert preview["data"]["package_artifact_written"] is False
    assert not (tmp_path / preview["data"]["package_artifact_path"]).exists()

    wrong = api.write_chaser_forge_marketplace_export_package("wrong")
    assert wrong["ok"] is True
    assert wrong["data"]["ok"] is False
    assert wrong["data"]["package_artifact_written"] is False
    assert "expected_package_digest_mismatch" in wrong["data"]["blockers"]
    assert not (tmp_path / wrong["data"]["package_artifact_path"]).exists()

    written = api.write_chaser_forge_marketplace_export_package(preview["data"]["package_digest_sha256"])
    artifact_path = tmp_path / written["data"]["package_artifact_path"]
    assert written["ok"] is True
    assert written["data"]["ok"] is True
    assert written["data"]["package_artifact_written"] is True
    assert written["data"]["package_digest_sha256"] == preview["data"]["package_digest_sha256"]
    assert artifact_path.is_file()

    import_preview = api.get_chaser_forge_marketplace_import_preview(written["data"]["package_artifact_path"])
    assert import_preview["ok"] is True
    assert import_preview["data"]["ok"] is True
    assert import_preview["data"]["package_digest_sha256"] == preview["data"]["package_digest_sha256"]
    assert import_preview["data"]["marketplace_publish_allowed"] is False
    assert import_preview["data"]["auto_install_allowed"] is False
    assert import_preview["data"]["registry_written"] is False
    assert import_preview["data"]["extension_files_written"] == []
    assert not (tmp_path / "runtime" / "forge" / "registry" / "extensions.json").exists()
    assert not (tmp_path / "extensions" / "ugc-campaign-studio").exists()

    inline_import = api.get_chaser_forge_marketplace_import_preview()
    assert inline_import["ok"] is True
    assert inline_import["data"]["ok"] is True
    assert inline_import["data"]["package_artifact_path"] == "inline_package_payload"


def test_studio_api_writes_and_ingests_chaser_forge_remote_distribution_index(tmp_path: Path) -> None:
    api = StudioAPI(tmp_path)

    preview = api.get_chaser_forge_marketplace_remote_distribution()
    assert preview["ok"] is True
    assert preview["data"]["ok"] is True
    assert preview["data"]["remote_index_artifact_written"] is False
    assert preview["data"]["remote_network_publish_allowed"] is False
    assert preview["data"]["payment_mutation_allowed"] is False
    assert preview["data"]["license_checkout_allowed"] is False

    wrong = api.write_chaser_forge_marketplace_remote_index("wrong")
    assert wrong["ok"] is True
    assert wrong["data"]["ok"] is False
    assert wrong["data"]["remote_index_artifact_written"] is False
    assert "expected_remote_index_digest_required_or_mismatched" in wrong["data"]["blockers"]

    written = api.write_chaser_forge_marketplace_remote_index(preview["data"]["remote_index_digest_sha256"])
    index_path = tmp_path / written["data"]["remote_index_artifact_path"]
    assert written["ok"] is True
    assert written["data"]["ok"] is True
    assert written["data"]["remote_index_artifact_written"] is True
    assert index_path.is_file()

    ingest_preview = api.ingest_chaser_forge_marketplace_remote_listing(
        written["data"]["remote_index_artifact_path"],
        written["data"]["remote_index_digest_sha256"],
        written["data"]["listing_digest_sha256"],
        "",
        write_listing=False,
    )
    assert ingest_preview["ok"] is True
    assert ingest_preview["data"]["ok"] is True
    assert ingest_preview["data"]["catalog_listing_written"] is False
    assert ingest_preview["data"]["publisher_attestation_verified"] is True

    wrong_ingest = api.ingest_chaser_forge_marketplace_remote_listing(
        written["data"]["remote_index_artifact_path"],
        written["data"]["remote_index_digest_sha256"],
        written["data"]["listing_digest_sha256"],
        "wrong",
        write_listing=True,
    )
    assert wrong_ingest["ok"] is True
    assert wrong_ingest["data"]["ok"] is False
    assert "operator_confirmation_required_or_mismatched" in wrong_ingest["data"]["blockers"]

    ingested = api.ingest_chaser_forge_marketplace_remote_listing(
        written["data"]["remote_index_artifact_path"],
        written["data"]["remote_index_digest_sha256"],
        written["data"]["listing_digest_sha256"],
        ingest_preview["data"]["operator_confirmation_text"],
        write_listing=True,
    )
    assert ingested["ok"] is True
    assert ingested["data"]["ok"] is True
    assert ingested["data"]["catalog_listing_written"] is True
    assert ingested["data"]["remote_listing_ingested"] is True
    assert ingested["data"]["package_install_allowed"] is False
    assert not (tmp_path / "runtime" / "forge" / "registry" / "extensions.json").exists()
    assert not (tmp_path / "extensions" / "ugc-campaign-studio").exists()

    library = api.get_chaser_forge_marketplace_local_library()
    assert library["ok"] is True
    assert library["data"]["library_item_count"] == 1
    assert library["data"]["items"][0]["source"] == "remote_verified_catalog"


def test_studio_api_writes_chaser_forge_hosted_export_bundle(tmp_path: Path) -> None:
    api = StudioAPI(tmp_path)

    preview = api.get_chaser_forge_marketplace_hosted_export_bundle()
    assert preview["ok"] is True
    assert preview["data"]["ok"] is True
    assert preview["data"]["hosted_bundle_artifact_written"] is False
    assert preview["data"]["manual_static_host_ready"] is True
    assert preview["data"]["remote_network_publish_allowed"] is False
    assert preview["data"]["payment_mutation_allowed"] is False
    assert preview["data"]["license_checkout_allowed"] is False

    wrong = api.write_chaser_forge_marketplace_hosted_export_bundle(
        preview["data"]["remote_index_digest_sha256"],
        "wrong",
    )
    assert wrong["ok"] is True
    assert wrong["data"]["ok"] is False
    assert wrong["data"]["hosted_bundle_artifact_written"] is False
    assert "expected_hosted_bundle_digest_required_or_mismatched" in wrong["data"]["blockers"]

    wrong_remote = api.write_chaser_forge_marketplace_hosted_export_bundle(
        "wrong",
        preview["data"]["hosted_bundle_digest_sha256"],
    )
    assert wrong_remote["ok"] is True
    assert wrong_remote["data"]["ok"] is False
    assert "expected_remote_index_digest_mismatch" in wrong_remote["data"]["blockers"]

    written = api.write_chaser_forge_marketplace_hosted_export_bundle(
        preview["data"]["remote_index_digest_sha256"],
        preview["data"]["hosted_bundle_digest_sha256"],
    )
    artifact_path = tmp_path / written["data"]["hosted_bundle_artifact_path"]
    assert written["ok"] is True
    assert written["data"]["ok"] is True
    assert written["data"]["hosted_bundle_artifact_written"] is True
    assert artifact_path.is_file()
    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert payload["hosted_bundle_digest_sha256"] == preview["data"]["hosted_bundle_digest_sha256"]
    assert payload["publication_manifest"]["network_publish_allowed"] is False
    assert payload["publication_manifest"]["credentials_included"] is False
    assert payload["payment_mutation_allowed"] is False
    assert payload["license_checkout_allowed"] is False
    assert not (tmp_path / "runtime" / "forge" / "registry" / "extensions.json").exists()
    assert not (tmp_path / "extensions" / "ugc-campaign-studio").exists()


def test_studio_api_writes_chaser_forge_static_host_publication(tmp_path: Path) -> None:
    api = StudioAPI(tmp_path)

    preview = api.get_chaser_forge_marketplace_static_host_publication()
    assert preview["ok"] is True
    assert preview["data"]["ok"] is True
    assert preview["data"]["static_publication_written"] is False
    assert preview["data"]["manual_upload_ready"] is True
    assert preview["data"]["network_upload_performed"] is False
    assert preview["data"]["remote_network_publish_allowed"] is False
    assert preview["data"]["external_registry_mutation_allowed"] is False
    assert preview["data"]["payment_mutation_allowed"] is False
    assert preview["data"]["license_checkout_allowed"] is False

    wrong = api.write_chaser_forge_marketplace_static_host_publication(
        preview["data"]["remote_index_digest_sha256"],
        preview["data"]["hosted_bundle_digest_sha256"],
        "wrong",
    )
    assert wrong["ok"] is True
    assert wrong["data"]["ok"] is False
    assert wrong["data"]["static_publication_written"] is False
    assert "expected_static_publication_digest_required_or_mismatched" in wrong["data"]["blockers"]

    wrong_hosted = api.write_chaser_forge_marketplace_static_host_publication(
        preview["data"]["remote_index_digest_sha256"],
        "wrong",
        preview["data"]["static_publication_digest_sha256"],
    )
    assert wrong_hosted["ok"] is True
    assert wrong_hosted["data"]["ok"] is False
    assert "expected_hosted_bundle_digest_mismatch" in wrong_hosted["data"]["blockers"]

    written = api.write_chaser_forge_marketplace_static_host_publication(
        preview["data"]["remote_index_digest_sha256"],
        preview["data"]["hosted_bundle_digest_sha256"],
        preview["data"]["static_publication_digest_sha256"],
    )
    publication_dir = tmp_path / written["data"]["static_publication_dir_path"]
    assert written["ok"] is True
    assert written["data"]["ok"] is True
    assert written["data"]["static_publication_written"] is True
    assert publication_dir.is_dir()
    assert (publication_dir / "index.json").is_file()
    assert (publication_dir / "README.md").is_file()
    assert (publication_dir / "hosted-bundle.json").is_file()
    assert (publication_dir / "publication-manifest.json").is_file()
    assert (publication_dir / "checksums.json").is_file()
    payload = json.loads((publication_dir / "publication-manifest.json").read_text(encoding="utf-8"))
    assert payload["static_publication_digest_sha256"] == preview["data"]["static_publication_digest_sha256"]
    assert payload["network_upload_performed"] is False
    assert payload["external_registry_mutation_allowed"] is False
    assert payload["payment_mutation_allowed"] is False
    assert payload["license_checkout_allowed"] is False
    assert payload["package_install_allowed"] is False
    assert not (tmp_path / "runtime" / "forge" / "registry" / "extensions.json").exists()
    assert not (tmp_path / "extensions" / "ugc-campaign-studio").exists()


def test_studio_api_writes_chaser_forge_static_host_upload_handoff(tmp_path: Path) -> None:
    api = StudioAPI(tmp_path)

    preview = api.get_chaser_forge_marketplace_static_host_upload_handoff()
    assert preview["ok"] is True
    assert preview["data"]["ok"] is True
    assert preview["data"]["upload_handoff_written"] is False
    assert preview["data"]["manual_upload_handoff_ready"] is True
    assert preview["data"]["network_upload_performed"] is False
    assert preview["data"]["network_upload_allowed"] is False
    assert preview["data"]["external_registry_mutation_allowed"] is False
    assert preview["data"]["payment_mutation_allowed"] is False

    wrong = api.write_chaser_forge_marketplace_static_host_upload_handoff(
        preview["data"]["remote_index_digest_sha256"],
        preview["data"]["hosted_bundle_digest_sha256"],
        preview["data"]["static_publication_digest_sha256"],
        "wrong",
    )
    assert wrong["ok"] is True
    assert wrong["data"]["ok"] is False
    assert wrong["data"]["upload_handoff_written"] is False
    assert "expected_upload_handoff_digest_required_or_mismatched" in wrong["data"]["blockers"]

    written = api.write_chaser_forge_marketplace_static_host_upload_handoff(
        preview["data"]["remote_index_digest_sha256"],
        preview["data"]["hosted_bundle_digest_sha256"],
        preview["data"]["static_publication_digest_sha256"],
        preview["data"]["upload_handoff_digest_sha256"],
    )
    assert written["ok"] is True
    assert written["data"]["ok"] is True
    assert written["data"]["upload_handoff_written"] is True
    assert (tmp_path / written["data"]["upload_handoff_json_path"]).is_file()
    assert (tmp_path / written["data"]["upload_handoff_markdown_path"]).is_file()
    assert written["data"]["static_publication_files_present"] is True
    assert written["data"]["network_upload_performed"] is False
    assert written["data"]["network_upload_allowed"] is False
    assert written["data"]["external_registry_mutation_allowed"] is False
    assert written["data"]["payment_mutation_allowed"] is False
    assert written["data"]["license_checkout_allowed"] is False
    assert written["data"]["package_install_allowed"] is False
    assert not (tmp_path / "runtime" / "forge" / "registry" / "extensions.json").exists()
    assert not (tmp_path / "extensions" / "ugc-campaign-studio").exists()


def test_studio_api_writes_chaser_forge_static_host_upload_receipt(tmp_path: Path) -> None:
    api = StudioAPI(tmp_path)

    preview = api.get_chaser_forge_marketplace_static_host_upload_receipt(
        "https://example.invalid/chaser-forge"
    )
    assert preview["ok"] is True
    assert preview["data"]["ok"] is True
    assert preview["data"]["upload_receipt_written"] is False
    assert preview["data"]["manual_upload_receipt_ready"] is True
    assert preview["data"]["required_operator_receipt_statement"]
    assert preview["data"]["network_fetch_performed"] is False
    assert preview["data"]["network_fetch_allowed"] is False
    assert preview["data"]["external_registry_mutation_allowed"] is False
    assert preview["data"]["payment_mutation_allowed"] is False

    wrong_digest = api.write_chaser_forge_marketplace_static_host_upload_receipt(
        preview["data"]["remote_index_digest_sha256"],
        preview["data"]["hosted_bundle_digest_sha256"],
        preview["data"]["static_publication_digest_sha256"],
        preview["data"]["upload_handoff_digest_sha256"],
        "wrong",
        preview["data"]["operator_uploaded_base_url"],
        preview["data"]["required_operator_receipt_statement"],
    )
    assert wrong_digest["ok"] is True
    assert wrong_digest["data"]["ok"] is False
    assert wrong_digest["data"]["upload_receipt_written"] is False
    assert "expected_upload_receipt_digest_required_or_mismatched" in wrong_digest["data"]["blockers"]

    wrong_statement = api.write_chaser_forge_marketplace_static_host_upload_receipt(
        preview["data"]["remote_index_digest_sha256"],
        preview["data"]["hosted_bundle_digest_sha256"],
        preview["data"]["static_publication_digest_sha256"],
        preview["data"]["upload_handoff_digest_sha256"],
        preview["data"]["upload_receipt_digest_sha256"],
        preview["data"]["operator_uploaded_base_url"],
        "wrong",
    )
    assert wrong_statement["ok"] is True
    assert wrong_statement["data"]["ok"] is False
    assert wrong_statement["data"]["upload_receipt_written"] is False
    assert "operator_receipt_statement_required_or_mismatched" in wrong_statement["data"]["blockers"]

    written = api.write_chaser_forge_marketplace_static_host_upload_receipt(
        preview["data"]["remote_index_digest_sha256"],
        preview["data"]["hosted_bundle_digest_sha256"],
        preview["data"]["static_publication_digest_sha256"],
        preview["data"]["upload_handoff_digest_sha256"],
        preview["data"]["upload_receipt_digest_sha256"],
        preview["data"]["operator_uploaded_base_url"],
        preview["data"]["required_operator_receipt_statement"],
    )
    assert written["ok"] is True
    assert written["data"]["ok"] is True
    assert written["data"]["upload_receipt_written"] is True
    assert (tmp_path / written["data"]["upload_receipt_json_path"]).is_file()
    assert (tmp_path / written["data"]["upload_receipt_markdown_path"]).is_file()
    assert written["data"]["operator_manual_upload_claim_recorded"] is True
    assert written["data"]["hosted_upload_verified_by_network_fetch"] is False
    assert written["data"]["network_fetch_performed"] is False
    assert written["data"]["network_fetch_allowed"] is False
    assert written["data"]["network_upload_allowed"] is False
    assert written["data"]["external_registry_mutation_allowed"] is False
    assert written["data"]["payment_mutation_allowed"] is False
    assert written["data"]["license_checkout_allowed"] is False
    assert written["data"]["package_install_allowed"] is False
    assert not (tmp_path / "runtime" / "forge" / "registry" / "extensions.json").exists()
    assert not (tmp_path / "extensions" / "ugc-campaign-studio").exists()


def test_studio_api_writes_chaser_forge_published_static_index_registration(tmp_path: Path) -> None:
    api = StudioAPI(tmp_path)

    preview = api.get_chaser_forge_marketplace_published_static_index_registration(
        "https://example.invalid/chaser-forge/index.json"
    )
    assert preview["ok"] is True
    assert preview["data"]["ok"] is True
    assert preview["data"]["published_static_index_registration_written"] is False
    assert preview["data"]["published_static_index_registration_ready"] is True
    assert preview["data"]["required_operator_registration_statement"]
    assert preview["data"]["live_url_verified"] is False
    assert preview["data"]["network_fetch_performed"] is False
    assert preview["data"]["network_fetch_allowed"] is False
    assert preview["data"]["external_registry_mutation_allowed"] is False
    assert preview["data"]["payment_mutation_allowed"] is False

    receipt_preview = api.get_chaser_forge_marketplace_static_host_upload_receipt(
        "https://example.invalid/chaser-forge"
    )
    assert receipt_preview["ok"] is True
    assert receipt_preview["data"]["ok"] is True

    wrong_digest = api.write_chaser_forge_marketplace_published_static_index_registration(
        preview["data"]["remote_index_digest_sha256"],
        preview["data"]["hosted_bundle_digest_sha256"],
        preview["data"]["static_publication_digest_sha256"],
        preview["data"]["upload_handoff_digest_sha256"],
        preview["data"]["upload_receipt_digest_sha256"],
        "wrong",
        preview["data"]["operator_published_static_index_url"],
        receipt_preview["data"]["required_operator_receipt_statement"],
        preview["data"]["required_operator_registration_statement"],
    )
    assert wrong_digest["ok"] is True
    assert wrong_digest["data"]["ok"] is False
    assert wrong_digest["data"]["published_static_index_registration_written"] is False
    assert "expected_published_static_index_registration_digest_required_or_mismatched" in wrong_digest["data"]["blockers"]

    wrong_statement = api.write_chaser_forge_marketplace_published_static_index_registration(
        preview["data"]["remote_index_digest_sha256"],
        preview["data"]["hosted_bundle_digest_sha256"],
        preview["data"]["static_publication_digest_sha256"],
        preview["data"]["upload_handoff_digest_sha256"],
        preview["data"]["upload_receipt_digest_sha256"],
        preview["data"]["published_static_index_registration_digest_sha256"],
        preview["data"]["operator_published_static_index_url"],
        receipt_preview["data"]["required_operator_receipt_statement"],
        "wrong",
    )
    assert wrong_statement["ok"] is True
    assert wrong_statement["data"]["ok"] is False
    assert wrong_statement["data"]["published_static_index_registration_written"] is False
    assert "operator_registration_statement_required_or_mismatched" in wrong_statement["data"]["blockers"]

    written = api.write_chaser_forge_marketplace_published_static_index_registration(
        preview["data"]["remote_index_digest_sha256"],
        preview["data"]["hosted_bundle_digest_sha256"],
        preview["data"]["static_publication_digest_sha256"],
        preview["data"]["upload_handoff_digest_sha256"],
        preview["data"]["upload_receipt_digest_sha256"],
        preview["data"]["published_static_index_registration_digest_sha256"],
        preview["data"]["operator_published_static_index_url"],
        receipt_preview["data"]["required_operator_receipt_statement"],
        preview["data"]["required_operator_registration_statement"],
    )
    assert written["ok"] is True
    assert written["data"]["ok"] is True
    assert written["data"]["published_static_index_registration_written"] is True
    assert (tmp_path / written["data"]["published_static_index_registration_json_path"]).is_file()
    assert (tmp_path / written["data"]["published_static_index_registration_markdown_path"]).is_file()
    assert written["data"]["operator_declared_published_index_registered"] is True
    assert written["data"]["live_url_verified"] is False
    assert written["data"]["network_fetch_performed"] is False
    assert written["data"]["network_fetch_allowed"] is False
    assert written["data"]["network_upload_allowed"] is False
    assert written["data"]["external_registry_mutation_allowed"] is False
    assert written["data"]["payment_mutation_allowed"] is False
    assert written["data"]["license_checkout_allowed"] is False
    assert written["data"]["package_install_allowed"] is False
    assert not (tmp_path / "runtime" / "forge" / "registry" / "extensions.json").exists()
    assert not (tmp_path / "extensions" / "ugc-campaign-studio").exists()


def test_studio_api_digest_gates_chaser_forge_marketplace_import_sandbox_approval(tmp_path: Path) -> None:
    api = StudioAPI(tmp_path)
    preview = api.get_chaser_forge_panel()["data"]["marketplace"]["import_approval_request"]

    wrong = api.request_chaser_forge_marketplace_import_sandbox_approval("wrong")
    assert wrong["ok"] is True
    assert wrong["data"]["ok"] is False
    assert wrong["data"]["approval_request_written"] is False
    assert "request_digest_required_or_mismatched" in wrong["data"]["blockers"]
    assert not (tmp_path / wrong["data"]["approval_artifact_path"]).exists()

    written = api.request_chaser_forge_marketplace_import_sandbox_approval(preview["request_digest_sha256"])
    artifact_path = tmp_path / written["data"]["approval_artifact_path"]
    assert written["ok"] is True
    assert written["data"]["ok"] is True
    assert written["data"]["approval_request_written"] is True
    assert artifact_path.is_file()
    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert payload["record_type"] == "forge_marketplace_import_sandbox_approval_request"
    assert payload["approval_scope"] == "forge.marketplace_import.sandbox_review"
    assert payload["package_install_allowed_in_this_pass"] is False
    assert payload["registry_write_allowed_in_this_pass"] is False
    assert payload["extension_file_write_allowed_in_this_pass"] is False
    assert written["data"]["package_install_allowed"] is False
    assert written["data"]["registry_written"] is False
    assert written["data"]["extension_files_written"] == []
    assert not (tmp_path / "runtime" / "forge" / "registry" / "extensions.json").exists()
    assert not (tmp_path / "extensions" / "ugc-campaign-studio").exists()


def test_studio_api_bridges_approved_marketplace_import_to_pending_sandbox_request_only(tmp_path: Path) -> None:
    api = StudioAPI(tmp_path)
    preview = api.get_chaser_forge_panel()["data"]["marketplace"]["import_approval_request"]
    request = api.request_chaser_forge_marketplace_import_sandbox_approval(preview["request_digest_sha256"])
    import_artifact_path = tmp_path / request["data"]["approval_artifact_path"]
    source_payload = json.loads(import_artifact_path.read_text(encoding="utf-8"))

    decision = api.review_chaser_forge_approval_decision(
        request["data"]["approval_artifact_path"],
        "approved",
        request["data"]["request_digest_sha256"],
        source_payload["operator_confirmation_text"],
        write_decision=True,
    )
    assert decision["ok"] is True

    bridge_preview = api.get_chaser_forge_marketplace_import_sandbox_request(
        request["data"]["approval_artifact_path"],
        request["data"]["request_digest_sha256"],
    )
    assert bridge_preview["ok"] is True
    assert bridge_preview["data"]["ok"] is True
    assert bridge_preview["data"]["sandbox_approval_request_written"] is False
    assert bridge_preview["data"]["marketplace_import_approval_consumed"] is False

    wrong = api.request_chaser_forge_marketplace_import_sandbox_request(
        request["data"]["approval_artifact_path"],
        request["data"]["request_digest_sha256"],
        "wrong",
    )
    assert wrong["ok"] is True
    assert wrong["data"]["ok"] is False
    assert wrong["data"]["sandbox_approval_request_written"] is False
    assert "request_digest_required_or_mismatched" in wrong["data"]["blockers"]

    written = api.request_chaser_forge_marketplace_import_sandbox_request(
        request["data"]["approval_artifact_path"],
        request["data"]["request_digest_sha256"],
        bridge_preview["data"]["request_digest_sha256"],
    )
    sandbox_artifact_path = tmp_path / written["data"]["sandbox_approval_artifact_path"]
    assert written["ok"] is True
    assert written["data"]["ok"] is True
    assert written["data"]["sandbox_approval_request_written"] is True
    assert sandbox_artifact_path.is_file()
    sandbox_payload = json.loads(sandbox_artifact_path.read_text(encoding="utf-8"))
    assert sandbox_payload["record_type"] == "forge_sandbox_install_approval_request"
    assert sandbox_payload["status"] == "pending_operator_decision"
    assert sandbox_payload["approval_consumed"] is False
    refreshed_import_payload = json.loads(import_artifact_path.read_text(encoding="utf-8"))
    assert refreshed_import_payload["status"] == "approved"
    assert refreshed_import_payload["approval_consumed"] is False
    assert written["data"]["registry_written"] is False
    assert written["data"]["extension_files_written"] == []
    assert written["data"]["exact_once_marker_reserved"] is False
    assert not (tmp_path / "runtime" / "forge" / "registry" / "extensions.json").exists()
    assert not (tmp_path / "extensions" / "ugc-campaign-studio").exists()


def test_studio_api_publishes_and_executes_governed_marketplace_install(tmp_path: Path) -> None:
    api = StudioAPI(tmp_path)

    publish_preview = api.get_chaser_forge_marketplace_publish_preview()
    assert publish_preview["ok"] is True
    assert publish_preview["data"]["ok"] is True

    wrong_publish = api.publish_chaser_forge_marketplace_package("wrong")
    assert wrong_publish["ok"] is True
    assert wrong_publish["data"]["ok"] is False
    assert "expected_listing_digest_required_or_mismatched" in wrong_publish["data"]["blockers"]

    published = api.publish_chaser_forge_marketplace_package(publish_preview["data"]["listing_digest_sha256"])
    assert published["ok"] is True
    assert published["data"]["ok"] is True
    assert published["data"]["catalog_listing_written"] is True

    catalog = api.get_chaser_forge_marketplace_catalog()
    assert catalog["ok"] is True
    assert catalog["data"]["entry_count"] == 1

    import_preview = api.get_chaser_forge_panel()["data"]["marketplace"]["import_approval_request"]
    import_request = api.request_chaser_forge_marketplace_import_sandbox_approval(
        import_preview["request_digest_sha256"]
    )
    import_payload = json.loads((tmp_path / import_request["data"]["approval_artifact_path"]).read_text(encoding="utf-8"))
    import_decision = api.review_chaser_forge_approval_decision(
        import_request["data"]["approval_artifact_path"],
        "approved",
        import_request["data"]["request_digest_sha256"],
        import_payload["operator_confirmation_text"],
        write_decision=True,
    )
    assert import_decision["data"]["decision_artifact_written"] is True

    bridge_preview = api.get_chaser_forge_marketplace_import_sandbox_request(
        import_request["data"]["approval_artifact_path"],
        import_request["data"]["request_digest_sha256"],
    )
    bridge = api.request_chaser_forge_marketplace_import_sandbox_request(
        import_request["data"]["approval_artifact_path"],
        import_request["data"]["request_digest_sha256"],
        bridge_preview["data"]["request_digest_sha256"],
    )
    sandbox_payload = json.loads((tmp_path / bridge["data"]["sandbox_approval_artifact_path"]).read_text(encoding="utf-8"))
    sandbox_decision = api.review_chaser_forge_approval_decision(
        bridge["data"]["sandbox_approval_artifact_path"],
        "approved",
        bridge["data"]["sandbox_request_digest_sha256"],
        sandbox_payload["operator_confirmation_text"],
        write_decision=True,
    )
    assert sandbox_decision["data"]["decision_artifact_written"] is True

    ready = api.execute_chaser_forge_marketplace_install(
        import_request["data"]["approval_artifact_path"],
        import_request["data"]["request_digest_sha256"],
        bridge["data"]["sandbox_approval_artifact_path"],
        bridge["data"]["sandbox_request_digest_sha256"],
        published["data"]["listing_digest_sha256"],
        published["data"]["listing_id"],
        bridge["data"]["request_digest_sha256"],
        execute=False,
    )
    assert ready["ok"] is True
    assert ready["data"]["ok"] is True, ready["data"]["blockers"]
    assert ready["data"]["marketplace_install_executed"] is False

    executed = api.execute_chaser_forge_marketplace_install(
        import_request["data"]["approval_artifact_path"],
        import_request["data"]["request_digest_sha256"],
        bridge["data"]["sandbox_approval_artifact_path"],
        bridge["data"]["sandbox_request_digest_sha256"],
        published["data"]["listing_digest_sha256"],
        published["data"]["listing_id"],
        bridge["data"]["request_digest_sha256"],
        execute=True,
    )
    assert executed["ok"] is True
    assert executed["data"]["marketplace_install_executed"] is True
    assert executed["data"]["registry_written"] is True
    assert executed["data"]["extension_files_written"]
    assert executed["data"]["marketplace_import_approval_consumed"] is True

    library = api.get_chaser_forge_marketplace_local_library()
    assert library["ok"] is True
    assert library["surface"] == "chaser_forge_marketplace_local_library"
    assert library["data"]["ok"] is True
    assert library["data"]["library_item_count"] == 1
    assert library["data"]["listed_installed_count"] == 1
    assert library["data"]["items"][0]["installed"] is True
    assert library["data"]["items"][0]["registry_status"] == "sandbox_installed"
    assert library["data"]["items"][0]["target_paths_existing_count"] == library["data"]["items"][0]["target_path_count"]
    assert library["data"]["authority"]["local_marketplace_library_read_only"] is True
    assert library["data"]["remote_marketplace_call_allowed"] is False


def test_studio_api_digest_gates_chaser_forge_sandbox_approval(tmp_path: Path) -> None:
    api = StudioAPI(tmp_path)
    preview = api.get_chaser_forge_panel()["data"]["sandbox_approval"]

    wrong = api.request_chaser_forge_sandbox_approval("wrong")
    assert wrong["ok"] is True
    assert wrong["data"]["approval_request_written"] is False
    assert "request_digest_required_or_mismatched" in wrong["data"]["blockers"]

    written = api.request_chaser_forge_sandbox_approval(preview["request_digest_sha256"])
    artifact_path = tmp_path / written["data"]["approval_artifact_path"]
    assert written["ok"] is True
    assert written["data"]["approval_request_written"] is True
    assert artifact_path.is_file()
    assert not (tmp_path / "runtime" / "forge" / "registry" / "extensions.json").exists()
    assert not (tmp_path / "extensions" / "ugc-campaign-studio").exists()


def test_studio_api_records_chaser_forge_decision_handoff_without_execution(tmp_path: Path) -> None:
    api = StudioAPI(tmp_path)
    preview = api.get_chaser_forge_panel()["data"]["sandbox_approval"]
    request = api.request_chaser_forge_sandbox_approval(preview["request_digest_sha256"])
    artifact_path = tmp_path / request["data"]["approval_artifact_path"]
    source_payload = json.loads(artifact_path.read_text(encoding="utf-8"))

    handoff = api.review_chaser_forge_approval_decision(
        request["data"]["approval_artifact_path"],
        "approved",
        preview["request_digest_sha256"],
        source_payload["operator_confirmation_text"],
        write_decision=True,
    )

    assert handoff["ok"] is True
    assert handoff["data"]["status"] == "forge_approval_decision_recorded"
    assert handoff["data"]["decision_artifact_written"] is True
    assert handoff["data"]["approval_artifact_mutated"] is True
    assert handoff["data"]["approval_consumed"] is False
    assert (tmp_path / handoff["data"]["decision_artifact_path"]).is_file()
    approved_payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert approved_payload["status"] == "approved"
    assert approved_payload["operator_decision"] == "approved"
    assert approved_payload["approval_consumed"] is False
    assert approved_payload["decision_artifact_path"] == handoff["data"]["decision_artifact_path"]
    assert not (tmp_path / "runtime" / "forge" / "registry" / "extensions.json").exists()
    assert not (tmp_path / "extensions" / "ugc-campaign-studio").exists()

    ready = api.execute_chaser_forge_sandbox_registry_write(preview["request_digest_sha256"], execute=False)
    assert ready["ok"] is True
    assert ready["data"]["registry_written"] is False


def test_studio_api_exposes_chaser_forge_operator_decision_form_without_writes(tmp_path: Path) -> None:
    api = StudioAPI(tmp_path)
    preview = api.get_chaser_forge_panel()["data"]["sandbox_approval"]
    request = api.request_chaser_forge_sandbox_approval(preview["request_digest_sha256"])
    artifact_path = tmp_path / request["data"]["approval_artifact_path"]
    source_payload = json.loads(artifact_path.read_text(encoding="utf-8"))

    form = api.get_chaser_forge_approval_decision_form(request["data"]["approval_artifact_path"])

    assert form["ok"] is True
    assert form["surface"] == "chaser_forge_approval_decision_form"
    assert form["data"]["surface"] == "chaser_forge_operator_decision_form"
    assert form["data"]["status"] == "forge_approval_decision_form_ready"
    assert form["data"]["source_specific"] is True
    assert form["data"]["generic_approval_center_control"] is False
    assert form["data"]["preview_only"] is True
    assert form["data"]["write_decision_enabled_by_form_preview"] is False
    assert form["data"]["approval_consumption_allowed"] is False
    assert form["data"]["forge_execution_allowed"] is False
    approved = next(item for item in form["data"]["decision_options"] if item["decision"] == "approved")
    assert approved["required_operator_statement"] == source_payload["operator_confirmation_text"]
    assert approved["submit_payload"]["approval_artifact_path"] == request["data"]["approval_artifact_path"]
    assert approved["submit_payload"]["expected_request_digest"] == preview["request_digest_sha256"]
    assert approved["submit_payload"]["write_decision"] is True
    unchanged_payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert unchanged_payload["status"] == "pending_operator_decision"
    assert not (tmp_path / "runtime" / "forge" / "registry" / "extensions.json").exists()
    assert not (tmp_path / approved["future_decision_artifact_path"]).exists()


def test_studio_api_executes_forge_sandbox_registry_writer_after_approved_artifact(tmp_path: Path) -> None:
    api = StudioAPI(tmp_path)
    preview = api.get_chaser_forge_panel()["data"]["sandbox_approval"]
    request = api.request_chaser_forge_sandbox_approval(preview["request_digest_sha256"])
    artifact_path = tmp_path / request["data"]["approval_artifact_path"]
    _approve_artifact(tmp_path, artifact_path)

    ready = api.execute_chaser_forge_sandbox_registry_write(preview["request_digest_sha256"], execute=False)
    assert ready["ok"] is True
    assert ready["data"]["registry_written"] is False

    executed = api.execute_chaser_forge_sandbox_registry_write(preview["request_digest_sha256"], execute=True)
    assert executed["ok"] is True
    assert executed["data"]["registry_written"] is True
    assert executed["data"]["approval_consumed"] is True
    assert (tmp_path / "runtime" / "forge" / "registry" / "extensions.json").is_file()
    assert (tmp_path / "extensions" / "ugc-campaign-studio" / "manifest.json").is_file()


def test_studio_api_writes_live_install_approval_after_sandbox_proof_only(tmp_path: Path) -> None:
    api = StudioAPI(tmp_path)
    preview = api.get_chaser_forge_panel()["data"]["sandbox_approval"]
    request = api.request_chaser_forge_sandbox_approval(preview["request_digest_sha256"])
    sandbox_artifact_path = tmp_path / request["data"]["approval_artifact_path"]
    _approve_artifact(tmp_path, sandbox_artifact_path)

    executed = api.execute_chaser_forge_sandbox_registry_write(preview["request_digest_sha256"], execute=True)
    assert executed["ok"] is True

    live_preview = api.get_chaser_forge_panel()["data"]["live_install_approval"]
    assert live_preview["ok"] is True
    wrong = api.request_chaser_forge_live_install_approval("wrong")
    assert wrong["ok"] is True
    assert wrong["data"]["approval_request_written"] is False
    assert "request_digest_required_or_mismatched" in wrong["data"]["blockers"]

    written = api.request_chaser_forge_live_install_approval(live_preview["request_digest_sha256"])
    live_artifact_path = tmp_path / written["data"]["approval_artifact_path"]
    assert written["ok"] is True
    assert written["data"]["approval_request_written"] is True
    assert live_artifact_path.is_file()
    live_payload = json.loads(live_artifact_path.read_text(encoding="utf-8"))
    assert live_payload["record_type"] == "forge_live_install_approval_request"
    assert live_payload["live_install_allowed_in_this_pass"] is False
    assert live_payload["live_install_executor_built"] is False
    assert not (tmp_path / written["data"]["future_live_exact_once_marker_path"]).exists()


def test_studio_api_executes_live_install_after_approved_live_artifact(tmp_path: Path) -> None:
    api = StudioAPI(tmp_path)
    preview = api.get_chaser_forge_panel()["data"]["sandbox_approval"]
    request = api.request_chaser_forge_sandbox_approval(preview["request_digest_sha256"])
    sandbox_artifact_path = tmp_path / request["data"]["approval_artifact_path"]
    _approve_artifact(tmp_path, sandbox_artifact_path)

    sandbox_executed = api.execute_chaser_forge_sandbox_registry_write(preview["request_digest_sha256"], execute=True)
    assert sandbox_executed["ok"] is True

    live_preview = api.get_chaser_forge_panel()["data"]["live_install_approval"]
    live_request = api.request_chaser_forge_live_install_approval(live_preview["request_digest_sha256"])
    live_artifact_path = tmp_path / live_request["data"]["approval_artifact_path"]
    _approve_artifact(tmp_path, live_artifact_path)

    ready = api.execute_chaser_forge_live_install(live_preview["request_digest_sha256"], execute=False)
    assert ready["ok"] is True
    assert ready["data"]["registry_updated"] is False

    executed = api.execute_chaser_forge_live_install(live_preview["request_digest_sha256"], execute=True)
    assert executed["ok"] is True
    assert executed["data"]["live_install_executed"] is True
    assert executed["data"]["approval_consumed"] is True
    assert executed["data"]["extension_files_written"] == []
    registry = json.loads((tmp_path / "runtime" / "forge" / "registry" / "extensions.json").read_text(encoding="utf-8"))
    assert registry["entries"][0]["registry_status"] == "live_installed"
    assert registry["entries"][0]["install_environment"] == "live"


def test_studio_api_executes_rollback_after_approved_rollback_artifact(tmp_path: Path) -> None:
    api = StudioAPI(tmp_path)
    preview = api.get_chaser_forge_panel()["data"]["sandbox_approval"]
    request = api.request_chaser_forge_sandbox_approval(preview["request_digest_sha256"])
    sandbox_artifact_path = tmp_path / request["data"]["approval_artifact_path"]
    _approve_artifact(tmp_path, sandbox_artifact_path)

    sandbox_executed = api.execute_chaser_forge_sandbox_registry_write(preview["request_digest_sha256"], execute=True)
    assert sandbox_executed["ok"] is True

    live_preview = api.get_chaser_forge_panel()["data"]["live_install_approval"]
    live_request = api.request_chaser_forge_live_install_approval(live_preview["request_digest_sha256"])
    live_artifact_path = tmp_path / live_request["data"]["approval_artifact_path"]
    _approve_artifact(tmp_path, live_artifact_path)
    live_executed = api.execute_chaser_forge_live_install(live_preview["request_digest_sha256"], execute=True)
    assert live_executed["ok"] is True

    rollback_preview = api.get_chaser_forge_panel()["data"]["rollback_approval"]
    assert rollback_preview["ok"] is True
    wrong = api.request_chaser_forge_rollback_approval("wrong")
    assert wrong["ok"] is True
    assert wrong["data"]["approval_request_written"] is False
    assert "request_digest_required_or_mismatched" in wrong["data"]["blockers"]

    rollback_request = api.request_chaser_forge_rollback_approval(rollback_preview["request_digest_sha256"])
    rollback_artifact_path = tmp_path / rollback_request["data"]["approval_artifact_path"]
    _approve_artifact(tmp_path, rollback_artifact_path)

    ready = api.execute_chaser_forge_rollback(rollback_preview["request_digest_sha256"], execute=False)
    assert ready["ok"] is True
    assert ready["data"]["registry_updated"] is False

    executed = api.execute_chaser_forge_rollback(rollback_preview["request_digest_sha256"], execute=True)
    assert executed["ok"] is True
    assert executed["data"]["rollback_executed"] is True
    assert executed["data"]["approval_consumed"] is True
    assert executed["data"]["extension_files_deleted"] == []
    registry = json.loads((tmp_path / "runtime" / "forge" / "registry" / "extensions.json").read_text(encoding="utf-8"))
    entry = registry["entries"][0]
    assert entry["registry_status"] == "sandbox_installed"
    assert entry["install_environment"] == "sandbox"
    assert "live_execution" not in entry
    assert entry["rollback_execution"]["rollback"] is True


def test_panel_registry_marks_chaser_forge_mounted(tmp_path: Path) -> None:
    registry = build_native_shell_panel_registry(tmp_path)
    panels = {panel["id"]: panel for panel in registry["panels"]}

    assert "chaser-forge" in panels
    assert panels["chaser-forge"]["read_only"] is False
    assert panels["chaser-forge"]["write_mode"] == "approval_gated"
    assert panels["chaser-forge"]["api_methods"] == [
        "get_chaser_forge_panel",
        "request_chaser_forge_sandbox_approval",
        "request_chaser_forge_live_install_approval",
        "request_chaser_forge_rollback_approval",
        "get_chaser_forge_approval_decision_form",
        "review_chaser_forge_approval_decision",
        "get_chaser_forge_marketplace_export_package",
        "write_chaser_forge_marketplace_export_package",
        "get_chaser_forge_marketplace_catalog",
        "get_chaser_forge_marketplace_local_library",
        "get_chaser_forge_marketplace_remote_distribution",
        "write_chaser_forge_marketplace_remote_index",
        "ingest_chaser_forge_marketplace_remote_listing",
        "get_chaser_forge_marketplace_hosted_export_bundle",
        "write_chaser_forge_marketplace_hosted_export_bundle",
        "get_chaser_forge_marketplace_static_host_publication",
        "write_chaser_forge_marketplace_static_host_publication",
        "get_chaser_forge_marketplace_static_host_upload_handoff",
        "write_chaser_forge_marketplace_static_host_upload_handoff",
        "get_chaser_forge_marketplace_static_host_upload_receipt",
        "write_chaser_forge_marketplace_static_host_upload_receipt",
        "get_chaser_forge_marketplace_published_static_index_registration",
        "write_chaser_forge_marketplace_published_static_index_registration",
        "get_chaser_forge_marketplace_live_index_input_prefill",
        "write_chaser_forge_marketplace_live_index_input_prefill",
        "get_chaser_forge_marketplace_live_index_input_readiness",
        "get_chaser_forge_no_domain_closeout_audit",
        "get_chaser_forge_marketplace_publish_preview",
        "publish_chaser_forge_marketplace_package",
        "get_chaser_forge_marketplace_import_preview",
        "request_chaser_forge_marketplace_import_sandbox_approval",
        "get_chaser_forge_marketplace_import_sandbox_request",
        "request_chaser_forge_marketplace_import_sandbox_request",
        "execute_chaser_forge_marketplace_install",
        "execute_chaser_forge_sandbox_registry_write",
        "execute_chaser_forge_live_install",
        "execute_chaser_forge_rollback",
    ]
    assert registry["readiness"]["chaser_forge_panel_mounted"] is True
    assert registry["readiness"]["chaser_forge_manifest_validator_ready"] is True
    assert registry["readiness"]["chaser_forge_protected_core_guard_ready"] is True
    assert registry["readiness"]["chaser_forge_registry_read_model_ready"] is True
    assert registry["readiness"]["chaser_forge_sandbox_approval_preview_ready"] is True
    assert registry["readiness"]["chaser_forge_sandbox_approval_queue_write_gated"] is True
    assert registry["readiness"]["chaser_forge_approved_sandbox_registry_writer_ready"] is True
    assert registry["readiness"]["chaser_forge_sandbox_registry_writer_requires_approved_artifact"] is True
    assert registry["readiness"]["chaser_forge_live_install_approval_packet_ready"] is True
    assert registry["readiness"]["chaser_forge_live_install_approval_requires_sandbox_proof"] is True
    assert registry["readiness"]["chaser_forge_approved_live_install_executor_ready"] is True
    assert registry["readiness"]["chaser_forge_live_install_executor_requires_approved_artifact"] is True
    assert registry["readiness"]["chaser_forge_unapproved_live_install_blocked"] is True
    assert registry["readiness"]["chaser_forge_rollback_approval_packet_ready"] is True
    assert registry["readiness"]["chaser_forge_rollback_approval_requires_live_proof"] is True
    assert registry["readiness"]["chaser_forge_approved_rollback_executor_ready"] is True
    assert registry["readiness"]["chaser_forge_rollback_executor_requires_approved_artifact"] is True
    assert registry["readiness"]["chaser_forge_unapproved_rollback_blocked"] is True
    assert registry["readiness"]["chaser_forge_live_install_executor_blocked"] is False
    assert registry["readiness"]["chaser_forge_rollback_executor_blocked"] is False
    assert registry["readiness"]["chaser_forge_unapproved_registry_writer_blocked"] is True
    assert registry["readiness"]["chaser_forge_registry_writer_blocked"] is False
    assert registry["readiness"]["chaser_forge_approval_center_decision_handoff_ready"] is True
    assert registry["readiness"]["chaser_forge_decision_handoff_source_specific"] is True
    assert registry["readiness"]["chaser_forge_decision_handoff_consumption_blocked"] is True
    assert registry["readiness"]["chaser_forge_operator_decision_form_ready"] is True
    assert registry["readiness"]["chaser_forge_operator_decision_form_source_specific"] is True
    assert registry["readiness"]["chaser_forge_operator_decision_form_generic_control_blocked"] is True
    assert registry["readiness"]["chaser_forge_operator_decision_form_write_blocked"] is True
    assert registry["readiness"]["chaser_forge_decision_bound_executor_validation_ready"] is True
    assert registry["readiness"]["chaser_forge_executor_requires_decision_sidecar"] is True
    assert registry["readiness"]["chaser_forge_installer_writes_blocked"] is True
    assert registry["readiness"]["chaser_forge_proof_deck_studio_clickthrough_ready"] is True
    assert registry["readiness"]["chaser_forge_proof_deck_log_only"] is True
    assert registry["readiness"]["chaser_forge_live_studio_control_proof_ready"] is True
    assert registry["readiness"]["chaser_forge_local_mvp_completion_status_available"] is True
    assert registry["readiness"]["chaser_forge_marketplace_export_package_ready"] is True
    assert registry["readiness"]["chaser_forge_marketplace_package_write_digest_gated"] is True
    assert registry["readiness"]["chaser_forge_marketplace_catalog_ready"] is True
    assert registry["readiness"]["chaser_forge_marketplace_local_library_ready"] is True
    assert registry["readiness"]["chaser_forge_marketplace_local_library_read_only"] is True
    assert registry["readiness"]["chaser_forge_marketplace_local_library_ui_wired"] is True
    assert registry["readiness"]["chaser_forge_marketplace_remote_distribution_ready"] is True
    assert registry["readiness"]["chaser_forge_marketplace_remote_index_digest_gated"] is True
    assert registry["readiness"]["chaser_forge_marketplace_remote_ingest_preview_ready"] is True
    assert registry["readiness"]["chaser_forge_marketplace_remote_ingest_digest_gated"] is True
    assert registry["readiness"]["chaser_forge_marketplace_remote_network_calls_blocked"] is True
    assert registry["readiness"]["chaser_forge_marketplace_remote_payment_mutation_blocked"] is True
    assert registry["readiness"]["chaser_forge_marketplace_hosted_export_bundle_ready"] is True
    assert registry["readiness"]["chaser_forge_marketplace_hosted_export_bundle_digest_gated"] is True
    assert registry["readiness"]["chaser_forge_marketplace_hosted_export_manual_static_ready"] is True
    assert registry["readiness"]["chaser_forge_marketplace_hosted_export_network_publish_blocked"] is True
    assert registry["readiness"]["chaser_forge_marketplace_hosted_export_payment_mutation_blocked"] is True
    assert registry["readiness"]["chaser_forge_marketplace_static_host_publication_ready"] is True
    assert registry["readiness"]["chaser_forge_marketplace_static_host_publication_digest_gated"] is True
    assert registry["readiness"]["chaser_forge_marketplace_static_host_publication_manual_upload_ready"] is True
    assert registry["readiness"]["chaser_forge_marketplace_static_host_publication_network_upload_blocked"] is True
    assert registry["readiness"]["chaser_forge_marketplace_static_host_publication_payment_mutation_blocked"] is True
    assert registry["readiness"]["chaser_forge_marketplace_static_upload_handoff_ready"] is True
    assert registry["readiness"]["chaser_forge_marketplace_static_upload_handoff_digest_gated"] is True
    assert registry["readiness"]["chaser_forge_marketplace_static_upload_handoff_manual_action_required"] is True
    assert registry["readiness"]["chaser_forge_marketplace_static_upload_handoff_network_upload_blocked"] is True
    assert registry["readiness"]["chaser_forge_marketplace_static_upload_handoff_external_registry_blocked"] is True
    assert registry["readiness"]["chaser_forge_marketplace_static_upload_receipt_ready"] is True
    assert registry["readiness"]["chaser_forge_marketplace_static_upload_receipt_digest_gated"] is True
    assert registry["readiness"]["chaser_forge_marketplace_static_upload_receipt_operator_statement_required"] is True
    assert registry["readiness"]["chaser_forge_marketplace_static_upload_receipt_network_fetch_blocked"] is True
    assert registry["readiness"]["chaser_forge_marketplace_static_upload_receipt_external_registry_blocked"] is True
    assert registry["readiness"]["chaser_forge_marketplace_published_static_index_registration_ready"] is True
    assert registry["readiness"]["chaser_forge_marketplace_published_static_index_registration_digest_gated"] is True
    assert registry["readiness"]["chaser_forge_marketplace_published_static_index_registration_operator_statement_required"] is True
    assert registry["readiness"]["chaser_forge_marketplace_published_static_index_registration_network_fetch_blocked"] is True
    assert registry["readiness"]["chaser_forge_marketplace_published_static_index_registration_external_registry_blocked"] is True
    assert registry["readiness"]["chaser_forge_marketplace_published_static_index_registration_live_url_unverified"] is True
    assert registry["readiness"]["chaser_forge_marketplace_publish_digest_gated"] is True
    assert registry["readiness"]["chaser_forge_marketplace_local_public_listing_ready"] is True
    assert registry["readiness"]["chaser_forge_marketplace_import_preview_ready"] is True
    assert registry["readiness"]["chaser_forge_marketplace_import_sandbox_approval_ready"] is True
    assert registry["readiness"]["chaser_forge_marketplace_import_sandbox_approval_digest_gated"] is True
    assert registry["readiness"]["chaser_forge_marketplace_import_sandbox_request_bridge_ready"] is True
    assert registry["readiness"]["chaser_forge_marketplace_import_sandbox_request_digest_gated"] is True
    assert registry["readiness"]["chaser_forge_marketplace_import_sandbox_request_writes_pending_sandbox_approval_only"] is True
    assert registry["readiness"]["chaser_forge_marketplace_install_executor_ready"] is True
    assert registry["readiness"]["chaser_forge_marketplace_install_requires_source_specific_decisions"] is True
    assert registry["readiness"]["chaser_forge_marketplace_governed_auto_install_ready"] is True
    assert registry["readiness"]["chaser_forge_marketplace_remote_calls_blocked"] is True
    assert registry["readiness"]["chaser_forge_marketplace_unauthorized_auto_install_blocked"] is True


def test_frontend_static_hooks_for_chaser_forge_panel() -> None:
    index_html = (REPO_ROOT / "runtime" / "studio" / "shell" / "frontend" / "index.html").read_text(encoding="utf-8")
    app_js = (REPO_ROOT / "runtime" / "studio" / "shell" / "frontend" / "app.js").read_text(encoding="utf-8")

    assert 'data-panel="chaser-forge"' in index_html
    assert 'id="panel-chaser-forge"' in index_html
    assert "Extensions" in index_html
    assert "Manage local ChaseOS extensions" in index_html
    assert "No ambient install" in index_html
    assert "get_chaser_forge_panel" in app_js
    assert "renderChaserForgeProductWorkbench" in app_js
    assert "productizeChaserForgePanelDom" in app_js
    assert "Extension Manager" in app_js
    assert "Record details" in app_js
    assert "Connection details" in app_js
    assert "Extension Operating Context" in app_js
    assert "Extension Readiness" in app_js
    assert "Extension Capability Coverage" in app_js
    assert 'data-chaser-forge-object-card="extension"' in app_js
    assert "renderChaserForgeInspectorContext" in app_js
    assert "Capability Summary" in app_js
    assert "Approval Routing" in app_js
    assert "review_chaser_forge_approval_decision" in app_js
    assert "data-decision-handoff-surface" in app_js
    assert "Decision Helper" in app_js
    assert "get_chaser_forge_approval_decision_form" in app_js
    assert "data-decision-form-surface" in app_js
    assert "Live Install Gate" in app_js
    assert "Rollback Gate" in app_js
    assert "Quality Evidence" in app_js
    assert "data-proof-deck-surface" in app_js
    assert "proof_deck" in app_js
    assert "Local build implemented" in app_js
    assert "Live control verified" in app_js
    assert "Local Catalog & Install" in app_js
    assert "Local Marketplace Library" in app_js
    assert "Manual Static Distribution" in app_js
    assert "data-marketplace-surface" in app_js
    assert "data-marketplace-library-surface" in app_js
    assert "data-marketplace-remote-surface" in app_js
    assert "get_chaser_forge_marketplace_export_package" in app_js
    assert "write_chaser_forge_marketplace_export_package" in app_js
    assert "get_chaser_forge_marketplace_catalog" in app_js
    assert "get_chaser_forge_marketplace_local_library" in app_js
    assert "get_chaser_forge_marketplace_remote_distribution" in app_js
    assert "write_chaser_forge_marketplace_remote_index" in app_js
    assert "ingest_chaser_forge_marketplace_remote_listing" in app_js
    assert "get_chaser_forge_marketplace_hosted_export_bundle" in app_js
    assert "write_chaser_forge_marketplace_hosted_export_bundle" in app_js
    assert "get_chaser_forge_marketplace_static_host_publication" in app_js
    assert "write_chaser_forge_marketplace_static_host_publication" in app_js
    assert "get_chaser_forge_marketplace_static_host_upload_handoff" in app_js
    assert "write_chaser_forge_marketplace_static_host_upload_handoff" in app_js
    assert "get_chaser_forge_marketplace_static_host_upload_receipt" in app_js
    assert "write_chaser_forge_marketplace_static_host_upload_receipt" in app_js
    assert "get_chaser_forge_marketplace_published_static_index_registration" in app_js
    assert "write_chaser_forge_marketplace_published_static_index_registration" in app_js
    assert "Create Local Index" in app_js
    assert "Add Verified Listing" in app_js
    assert "Create Hosted Bundle" in app_js
    assert "Prepare Static Site" in app_js
    assert "Create Upload Handoff" in app_js
    assert "Record Upload Receipt" in app_js
    assert "Register Published Index" in app_js
    assert "Static publication" in app_js
    assert "Upload handoff" in app_js
    assert "Upload receipt" in app_js
    assert "Published index registration" in app_js
    assert "setChaserForgeRemoteStatus" in app_js
    assert "get_chaser_forge_marketplace_publish_preview" in app_js
    assert "publish_chaser_forge_marketplace_package" in app_js
    assert "get_chaser_forge_marketplace_import_preview" in app_js
    assert "request_chaser_forge_marketplace_import_sandbox_approval" in app_js
    assert "get_chaser_forge_marketplace_import_sandbox_request" in app_js
    assert "request_chaser_forge_marketplace_import_sandbox_request" in app_js
    assert "execute_chaser_forge_marketplace_install" in app_js
    assert "Run Governed Install" in app_js
    assert "setChaserForgeMarketplaceStatus" in app_js
    assert "marketplace" in app_js
    assert "loadChaserForgePanel" in app_js
    assert "Sandbox Review" in app_js
    assert "sandbox_approval" in app_js
    assert "sandbox_registry_writer" in app_js
    assert "live_install_approval" in app_js
    assert "live_install_executor" in app_js
    assert "rollback_approval" in app_js
    assert "rollback_executor" in app_js
