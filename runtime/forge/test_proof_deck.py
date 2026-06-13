from __future__ import annotations

import json
import os
from pathlib import Path

from runtime.forge.proof_deck import (
    BUILD_LOG_RELATIVE_PATHS,
    DEFAULT_SLUG,
    DOC_RELATIVE_PATHS,
    HOSTED_MARKETPLACE_EXPORT_BUNDLE_SMOKE_RESULT_RELATIVE_PATH,
    LIVE_STUDIO_CONTROL_PROOF_FALLBACK_REPORT_RELATIVE_PATH,
    MARKETPLACE_BRIDGE_VISUAL_QA_FALLBACK_REPORT_RELATIVE_PATH,
    MARKETPLACE_BRIDGE_VISUAL_QA_REPORT_RELATIVE_PATH,
    LOCAL_MARKETPLACE_LIBRARY_SMOKE_RESULT_RELATIVE_PATH,
    OPERATOR_USE_CLOSEOUT_SMOKE_RESULT_RELATIVE_PATH,
    OPERATOR_USE_STUDIO_PROOF_REPORT_RELATIVE_PATH,
    OUTPUT_ROOT,
    PUBLISHED_STATIC_INDEX_REGISTRATION_SMOKE_RESULT_RELATIVE_PATH,
    REMOTE_DISTRIBUTION_SMOKE_RESULT_RELATIVE_PATH,
    STATIC_HOST_PUBLICATION_SMOKE_RESULT_RELATIVE_PATH,
    STATIC_UPLOAD_HANDOFF_SMOKE_RESULT_RELATIVE_PATH,
    STATIC_UPLOAD_RECEIPT_SMOKE_RESULT_RELATIVE_PATH,
    VISUAL_QA_REPORT_RELATIVE_PATH,
    build_chaser_forge_proof_deck,
    render_chaser_forge_proof_deck_markdown,
)


def _write(path: Path, text: str) -> None:
    target = _io_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def _io_path(path: Path) -> Path:
    resolved = path.resolve()
    if os.name == "nt" and not str(resolved).startswith("\\\\?\\"):
        return Path("\\\\?\\" + str(resolved))
    return resolved


def _seed_required_evidence(vault: Path) -> None:
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
            "framework_overlay_detected": False,
            "console_errors_or_warnings": [],
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
        "fixture_evidence": {
            "registry_exists": True,
            "extension_files_written": ["extensions/ugc-campaign-studio/manifest.json"],
            "marketplace_import_approvals_consumed": [True],
            "sandbox_approvals_consumed": [True],
            "sandbox_marker_count": 1,
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
                "step": "initial",
                "viewport": "desktop",
                "path": "07_LOGS/Studio-Visual-QA/test/operator-initial.png",
                "bytes": 120,
                "not_blank": True,
                "marketplace_section_visible": True,
                "framework_overlay_detected": False,
                "status_text": "",
                "status_state": "",
            },
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
    _write(vault / "07_LOGS/Studio-Visual-QA/test/operator-initial.png", "desktop")
    _write(vault / "07_LOGS/Studio-Visual-QA/test/operator-publish.png", "desktop")
    _write(vault / "07_LOGS/Studio-Visual-QA/test/operator-mobile.png", "mobile")


def _snapshot(vault: Path) -> list[str]:
    return sorted(path.relative_to(vault).as_posix() for path in vault.rglob("*") if path.is_file())


def test_proof_deck_dry_run_packages_existing_evidence_without_writes(tmp_path: Path) -> None:
    _seed_required_evidence(tmp_path)
    before = _snapshot(tmp_path)

    deck = build_chaser_forge_proof_deck(
        tmp_path,
        generated_at="2026-05-20T14:00:00Z",
    )

    assert deck["ok"] is True
    assert deck["feature_status"] == "COMPLETE / GOVERNED CHASER FORGE MARKETPLACE, PUBLISHED STATIC INDEX REGISTRATION, STATIC HOST UPLOAD RECEIPT, STATIC HOST UPLOAD HANDOFF, STATIC HOST PUBLICATION PROOF, HOSTED EXPORT BUNDLE, REMOTE DISTRIBUTION FOUNDATION, AND STUDIO UI VERIFIED"
    assert deck["write_executed"] is False
    assert deck["read_only"] is True
    assert deck["writes"] == []
    assert deck["visual_qa"]["artifact_count"] == 5
    assert deck["marketplace_bridge_visual_qa"]["sandbox_approval_request_written"] is True
    assert deck["marketplace_bridge_visual_qa"]["marketplace_import_approval_consumed"] is False
    assert deck["marketplace_bridge_visual_qa"]["registry_written"] is False
    assert deck["live_studio_control_proof"]["sandbox_registry_written"] is True
    assert deck["live_studio_control_proof"]["live_install_executed"] is True
    assert deck["live_studio_control_proof"]["rollback_executed"] is True
    assert deck["live_studio_control_proof"]["catalog_listing_written"] is True
    assert deck["live_studio_control_proof"]["marketplace_install_registry_written"] is True
    assert deck["operator_use_studio_proof"]["publish_status_visible_after_refresh"] is True
    assert deck["operator_use_studio_proof"]["install_status_visible_after_refresh"] is True
    assert deck["operator_use_studio_proof"]["fixture_registry_written"] is True
    assert deck["operator_use_closeout_smoke"]["ok"] is True
    assert deck["operator_use_closeout_smoke"]["failures"] == []
    assert deck["local_marketplace_library_smoke"]["ok"] is True
    assert deck["local_marketplace_library_smoke"]["library_item_count"] == 1
    assert deck["remote_distribution_smoke"]["ok"] is True
    assert deck["remote_distribution_smoke"]["library_item_count"] == 1
    assert deck["hosted_marketplace_export_bundle_smoke"]["ok"] is True
    assert deck["hosted_marketplace_export_bundle_smoke"]["entry_count"] == 1
    assert deck["static_host_publication_smoke"]["ok"] is True
    assert deck["static_host_publication_smoke"]["file_count"] == 5
    assert deck["static_upload_handoff_smoke"]["ok"] is True
    assert deck["static_upload_handoff_smoke"]["file_count"] == 5
    assert deck["static_upload_receipt_smoke"]["ok"] is True
    assert deck["static_upload_receipt_smoke"]["file_count"] == 5
    assert deck["static_upload_receipt_smoke"]["upload_receipt_digest_sha256"] == "receipt"
    assert deck["published_static_index_registration_smoke"]["ok"] is True
    assert deck["published_static_index_registration_smoke"]["file_count"] == 5
    assert deck["published_static_index_registration_smoke"]["published_static_index_registration_digest_sha256"] == "registration"
    assert any(item["kind"] == "marketplace_bridge_visual_qa_report" for item in deck["evidence_matrix"])
    assert any(item["kind"] == "live_studio_control_proof_report" for item in deck["evidence_matrix"])
    assert any(item["kind"] == "operator_use_studio_proof_report" for item in deck["evidence_matrix"])
    assert any(item["kind"] == "operator_use_closeout_smoke_result" for item in deck["evidence_matrix"])
    assert any(item["kind"] == "local_marketplace_library_smoke_result" for item in deck["evidence_matrix"])
    assert any(item["kind"] == "remote_distribution_smoke_result" for item in deck["evidence_matrix"])
    assert any(item["kind"] == "hosted_marketplace_export_bundle_smoke_result" for item in deck["evidence_matrix"])
    assert any(item["kind"] == "static_host_publication_smoke_result" for item in deck["evidence_matrix"])
    assert any(item["kind"] == "static_upload_handoff_smoke_result" for item in deck["evidence_matrix"])
    assert any(item["kind"] == "static_upload_receipt_smoke_result" for item in deck["evidence_matrix"])
    assert any(item["kind"] == "published_static_index_registration_smoke_result" for item in deck["evidence_matrix"])
    assert set(deck["visual_qa"]["lifecycle_statuses"]) == {
        "approved_pending_execution",
        "consumed",
        "invalid_packet",
        "pending_operator_review",
        "rejected",
    }
    assert all(deck["authority"][flag] is False for flag in deck["authority"] if flag.endswith("_allowed") and flag != "proof_deck_log_artifact_write_allowed")
    assert _snapshot(tmp_path) == before


def test_proof_deck_write_stays_under_workflow_proofs(tmp_path: Path) -> None:
    _seed_required_evidence(tmp_path)

    deck = build_chaser_forge_proof_deck(
        tmp_path,
        generated_at="2026-05-20T14:05:00Z",
        write=True,
    )

    assert deck["ok"] is True
    assert deck["write_executed"] is True
    assert len(deck["writes"]) == 2
    assert all(path.startswith(OUTPUT_ROOT.as_posix()) for path in deck["writes"])
    assert deck["writes"] == [
        f"{OUTPUT_ROOT.as_posix()}/{DEFAULT_SLUG}.md",
        f"{OUTPUT_ROOT.as_posix()}/{DEFAULT_SLUG}.json",
    ]
    markdown_path = tmp_path / deck["markdown_path"]
    json_path = tmp_path / deck["json_path"]
    assert markdown_path.is_file()
    assert json_path.is_file()
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "forge.proof_deck.v1"
    assert payload["authority"]["approval_execution_allowed"] is False
    assert "Chaser Forge Proof Deck" in markdown_path.read_text(encoding="utf-8")


def test_proof_deck_reports_missing_visual_evidence(tmp_path: Path) -> None:
    for rel_path in BUILD_LOG_RELATIVE_PATHS:
        _write(tmp_path / rel_path, f"# {rel_path.stem}\n\n- Status: PARTIAL / VERIFIED\n")
    for rel_path in DOC_RELATIVE_PATHS:
        _write(tmp_path / rel_path, f"# {rel_path.stem}\n\nStatus: PARTIAL / VERIFIED\n")

    deck = build_chaser_forge_proof_deck(tmp_path, generated_at="2026-05-20T14:10:00Z")

    assert deck["ok"] is False
    assert deck["status"] == "PARTIAL / PROOF DECK BLOCKED BY MISSING EVIDENCE"
    assert "visual_qa_report_missing_or_unreadable" in deck["blockers"]
    assert "marketplace_bridge_visual_qa_report_missing_or_unreadable" in deck["blockers"]
    assert "operator_use_studio_proof_missing_or_unreadable" in deck["blockers"]
    assert "operator_use_closeout_smoke_missing_or_unreadable" in deck["blockers"]
    assert "live_studio_control_proof_missing_or_unreadable" in deck["blockers"]
    assert any(blocker.startswith("missing_required_evidence:") for blocker in deck["blockers"])


def test_proof_deck_markdown_lists_authority_boundary(tmp_path: Path) -> None:
    _seed_required_evidence(tmp_path)
    deck = build_chaser_forge_proof_deck(tmp_path, generated_at="2026-05-20T14:15:00Z")

    markdown = render_chaser_forge_proof_deck_markdown(deck)

    assert "No approval consumption or Forge executor is run by the proof deck." in markdown
    assert "Marketplace Bridge Visual QA Summary" in markdown
    assert "Live Studio Control Proof Summary" in markdown
    assert "Operator Use Closeout Smoke Summary" in markdown
    assert "Static Host Publication Smoke Summary" in markdown
    assert "Static Upload Receipt Smoke Summary" in markdown
    assert "Forbidden authority flags held false" in markdown
